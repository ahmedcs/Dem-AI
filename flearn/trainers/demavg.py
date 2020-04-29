import numpy as np
from tqdm import trange, tqdm
import tensorflow as tf
from flearn.utils.tf_utils import process_grad
from flearn.optimizer.proxsgd import PROXSGD
from .dembase import DemBase
from flearn.utils.DTree import Node
import matplotlib.pyplot as plt
from clustering.Setting import *
from clustering.Setting import *
from ..optimizer.dempgd import DemPerturbedGradientDescent
from ..optimizer.pgd import PerturbedGradientDescent
from utils.data_plot import *


class Server(DemBase):
    def __init__(self, params, learner, dataset):
        self.gamma = 1.  # soft or hard update in hierrachical averaging
        self.beta = 1.

        if (params['optimizer'] == "demavg"):
            print('Using DemAvg to Train')
            self.alg = "DEMAVG"
            self.inner_opt = tf.train.GradientDescentOptimizer(params['learning_rate'])
        elif (params['optimizer'] == "demprox"):
            self.mu = 0.004  # params['mu'] 0.002 (better generaliztaion) vs 0.005 (better specialization)
            print('Using DemProx to Train')
            self.alg = "DEMPROX"
            self.inner_opt = DemPerturbedGradientDescent(params['learning_rate'], mu=self.mu)

        super(Server, self).__init__(params, learner, dataset)

    def train(self):
        '''Train using Federated Averaging'''
        print("Train using " + self.alg)
        print('Training with {} workers ---'.format(self.clients_per_round))

        # for i in trange(self.num_rounds, desc='Round: ', ncols=120):
        for i in range(self.num_rounds):
            # test model
            if i % self.eval_every == 0:
                # ============= Test each client =============
                tqdm.write('============= Test Client Models - Specialization ============= ')
                stest_acu, strain_acc = self.evaluating_clients(i, mode="spe")
                self.cs_avg_data_test.append(stest_acu)
                self.cs_avg_data_train.append(strain_acc)
                tqdm.write('============= Test Client Models - Generalization ============= ')
                gtest_acu, gtrain_acc = self.evaluating_clients(i, mode="gen")
                self.cg_avg_data_test.append(gtest_acu)
                self.cg_avg_data_train.append(gtrain_acc)

                # ============= Test root =============
                if (i > 0):
                    tqdm.write('============= Test Group Models - Specialization ============= ')
                    self.evaluating_groups(self.TreeRoot, i, mode="spe")
                    gs_test = self.test_accs / self.count_grs
                    gs_train = self.train_accs / self.count_grs
                    self.gs_data_test.append(gs_test)
                    self.gs_data_train.append(gs_train)
                    print("AvgG. Testing performance for each level:", gs_test)
                    print("AvgG. Training performance for each level:", gs_train)
                    tqdm.write('============= Test Group Models - Generalization ============= ')
                    self.evaluating_groups(self.TreeRoot, i, mode="gen")
                    gg_test = self.test_accs / self.count_grs
                    gg_train = self.train_accs / self.count_grs
                    self.gg_data_test.append(gg_test)
                    self.gg_data_train.append(gg_train)
                    print("AvgG. Testing performance for each level:", gg_test)
                    print("AvgG. Training performance for each level:", gg_train)

                # self.rs_glob_acc.append(np.sum(stats[3])*1.0/np.sum(stats[2]))
                # self.rs_train_acc.append(np.sum(stats_train[3])*1.0/np.sum(stats_train[2]))
                # self.rs_train_loss.append(np.dot(stats_train[4], stats_train[2])*1.0/np.sum(stats_train[2]))
                #
                # model_len = process_grad(self.latest_model).size
                # global_grads = np.zeros(model_len)
                # client_grads = np.zeros(model_len)
                # num_samples = []
                # local_grads = []
                #
                # for c in self.clients:
                #     num, client_grad = c.get_grads(model_len)
                #     local_grads.append(client_grad)
                #     num_samples.append(num)
                #     global_grads = np.add(global_grads, client_grads * num)
                # global_grads = global_grads * 1.0 / np.sum(np.asarray(num_samples))
                #
                # difference = 0
                # for idx in range(len(self.clients)):
                #     difference += np.sum(np.square(global_grads - local_grads[idx]))
                # difference = difference * 1.0 / len(self.clients)
                # tqdm.write('gradient difference: {}'.format(difference))
                #
                # # save server model
                # self.metrics.write()
                # self.save()

            # choose K clients prop to data size
            # selected_clients = self.select_clients(i, num_clients=self.clients_per_round)
            selected_clients = self.clients

            csolns = []  # buffer for receiving client solutions
            cgrads = []
            for c in selected_clients:
                # for c in tqdm(selected_clients, desc='Client: ', leave=False, ncols=120):
                # communicate the latest model

                if (i == 0):
                    c.set_params(self.latest_model)
                else:
                    # Initialize the model of client based on hierrachical GK
                    init_w = (1 - self.beta) * (c.model.get_params()[0])
                    init_b = (1 - self.beta) * (c.model.get_params()[1])
                    hm = self.get_hierrachical_params(c)
                    # print(hm)
                    init_w += self.beta * hm[0]
                    init_b += self.beta * hm[1]
                    c.set_params((init_w, init_b))
                    # c.set_params(self.TreeRoot.gmodel)
                    # c.set_params(self.latest_model)

                # solve minimization locally
                # soln, grads, stats  = c.solve_inner(
                #     self.optimizer, num_epochs=self.num_epochs, batch_size=self.batch_size)  #Local round
                #
                # # gather solutions from client
                # csolns.append(soln)
                # cgrads.append(grads)

                _, _, stats = c.solve_inner(
                    self.optimizer, num_epochs=self.num_epochs, batch_size=self.batch_size)  # Local round

                # track communication cost
                self.metrics.update(rnd=i, cid=c.id, stats=stats)
            # print("First Client model:", np.sum(csolns[0][1][0]), np.sum(csolns[0][1][1]))
            if (i % TREE_UPDATE_PERIOD == 0):
                print("DEM-AI --------->>>>> Clustering")
                self.hierrachical_clustering(i)
                # self.TreeRoot.print_structure()
                print("DEM-AI --------->>>>> Hard Update generalized model")
                self.update_generalized_model(self.TreeRoot)  # hard update
                # print("Root Model:", np.sum(self.TreeRoot.gmodel[0]),np.sum(self.TreeRoot.gmodel[1]))
            else:
                # update model
                # self.latest_model = self.aggregate(csolns,weighted=True)
                print("DEM-AI --------->>>>> Soft Update generalized model")
                self.update_generalized_model(self.TreeRoot, mode="soft")  # soft update
                # print("Root Model:", np.sum(self.TreeRoot.gmodel[0]),np.sum(self.TreeRoot.gmodel[1]))

        self.save_results()
        # # final test model
        # stats = self.test()
        # # stats_train = self.train_error()
        # # stats_loss = self.train_loss()
        # stats_train = self.train_error_and_loss()
        #
        # self.metrics.accuracies.append(stats)
        # self.metrics.train_accuracies.append(stats_train)
        # tqdm.write('At round {} accuracy: {}'.format(self.num_rounds, np.sum(stats[3])*1.0/np.sum(stats[2])))
        # tqdm.write('At round {} training accuracy: {}'.format(self.num_rounds, np.sum(stats_train[3])*1.0/np.sum(stats_train[2])))
        # # save server model
        # self.metrics.write()
        # #self.save()
        # self.save(learning_rate=self.parameters["learning_rate"])
        #
        # print("Test ACC:", self.rs_glob_acc)
        # print("Training ACC:", self.rs_train_acc)
        # print("Training Loss:", self.rs_train_loss)

    def save_results(self):
        #file_name = "../results/ALG_"+RUNNING_ALG+'_ITER_'+NUM_GLOBAL_ITERS+'_UE_'+N_clients+'_K_'+K_Levels+'_w.h5'
        if(CLUSTER_METHOD == "weight"):
            file_name = "./results/{}_iter_{}_k_{}_w.h5".format(RUNNING_ALG, NUM_GLOBAL_ITERS, K_Levels)
        else:
            file_name = "./results/{}_iter_{}_k_{}_g.h5".format(RUNNING_ALG, NUM_GLOBAL_ITERS, K_Levels)
        print(file_name)
        root_train = np.asarray(self.gs_data_train)[:, -1]
        root_test = np.asarray(self.gs_data_test)[:, -1]

        write_file(file_name=file_name, root_test=root_test, root_train = root_train,
                   cs_avg_data_test=self.cs_avg_data_test, cs_avg_data_train=self.cs_avg_data_train,
                   cg_avg_data_test = self.cg_avg_data_test, cg_avg_data_train = self.cg_avg_data_train,
                   cs_data_test=self.cs_data_test, cs_data_train=self.cs_data_train, cg_data_test=self.cg_data_test,
                   cg_data_train=self.cg_data_train, g_level_train=self.g_level_train, g_level_test=self.g_level_test,
                   dendo_data=self.dendo_data, dendo_data_round=self.dendo_data_round,                                  #Dendrogram data
                   N_clients=[N_clients], TREE_UPDATE_PERIOD=[TREE_UPDATE_PERIOD])                                      #Setting



