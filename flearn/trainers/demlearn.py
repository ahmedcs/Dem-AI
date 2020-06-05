from tqdm import tqdm
import tensorflow as tf
from .dembase1 import DemBase
from ..optimizer.dempgd import DemPerturbedGradientDescent
# from utils.data_plot_mnist import *
from utils.dem_plot import *


class Server(DemBase):
    def __init__(self, params, learner, dataset):
        # self.gamma = 0.6  # soft update in hierrachical averaging
        self.gamma = PARAMS_gamma # hard update in hierrachical averaging
        self.beta = PARAMS_beta

        if (params['optimizer'] == "demlearn"):
            print('Using DemLearnto Train')
            self.alg = "Demlearn"
            self.inner_opt = tf.train.GradientDescentOptimizer(params['learning_rate'])
        elif (params['optimizer'] == "demlearn-p"):
            self.mu = PARAMS_mu
            # if(DATASET=="mnist"):
            #     self.mu =  params['mu'] # 0.005, 0.002, 0.001, 0.0005  => choose 0.002
            #     if (N_clients == 100):
            #         self.mu = 0.0005
            # elif(DATASET=="fmnist"):
            #     self.mu = 0.001 # 0.005, 0.002, 0.001, 0.0005  => select 0.001
            # else:
            #     self.mu = 0.001

            print('Using DemLearn-P to Train')
            self.alg = "Demlearn-p"
            self.inner_opt = DemPerturbedGradientDescent(params['learning_rate'], mu=self.mu)

        super(Server, self).__init__(params, learner, dataset)

    def train(self):
        '''Train using DemAVG or DemProx'''
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
                    # gs_test = self.test_accs / self.count_grs
                    # gs_train = self.train_accs / self.count_grs
                    # self.gs_data_test.append(gs_test)
                    # self.gs_data_train.append(gs_train)
                    self.gs_level_train[:,i,0] = self.gs_level_train[:,i,0] / self.gs_level_train[:,i,1]    #averaging by level and numb of clients
                    self.gs_level_test[:,i,0] = self.gs_level_test[:,i,0] / self.gs_level_test[:,i,1]       #averaging by level and numb of clients
                    print("AvgG. Testing performance for each level:", self.gs_level_test[:,i,0])
                    # print("AvgG. Training performance for each level:", self.gs_level_train[:,i,0])
                    tqdm.write('============= Test Group Models - Generalization ============= ')
                    self.evaluating_groups(self.TreeRoot, i, mode="gen")
                    # gg_test = self.test_accs / self.count_grs
                    # gg_train = self.train_accs / self.count_grs
                    # self.gg_data_test.append(gg_test)
                    # self.gg_data_train.append(gg_train)
                    self.gg_level_train[:,i,0] = self.gg_level_train[:,i,0] / self.gg_level_train[:,i,1]    #averaging by level and numb of clients
                    self.gg_level_test[:,i,0] = self.gg_level_test[:,i,0] / self.gg_level_test[:,i,1]       #averaging by level and numb of clients
                    print("AvgG. Testing performance for each level:", self.gg_level_test[:,i,0])
                    # print("AvgG. Training performance for each level:", self.gg_level_train[:,i,0])


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
                    init_w=[]
                    hm = self.get_hierrachical_params(c)
                    for w in range(len(self.model_shape1)):
                        init_w.append((1 - self.beta) * (c.model.get_params()[w]) + self.beta * hm[w])

                    c.set_params(tuple(init_w))

                _, _, stats = c.solve_inner(
                    self.optimizer, num_epochs=self.num_epochs, batch_size=self.batch_size)  # Local round

                # track communication cost
                self.metrics.update(rnd=i, cid=c.id, stats=stats)
            # print("First Client model:", np.sum(csolns[0][1][0]), np.sum(csolns[0][1][1]))
            # if (i % 3 == 0 and DECAY == True):
            #     self.gamma = max(self.gamma - 0.3, 0.05)  # period = 3, 0.960  vs 0.945.. after 31
            #     # self.gamma = self.gamma *0.2  # max(self.gamma *0.5,0.05)
            if (DECAY == True):
                if(DATASET=="mnist"):
                    self.beta = max(self.beta *0.7,0.001) #### Mnist dataset
                elif(DATASET == "fmnist"):
                    self.beta = max(self.beta * 0.5, 0.0005)  #### Mnist dataset
                # self.gamma = max(self.gamma - 0.25, 0.02)  # period = 2  0.96 vs 0.9437 after 31 : 0.25, 0.02 DemAVG
                # self.gamma = max(self.gamma - 0.1, 0.6) # 0.25, 0.02:  0.987 vs 0.859 after 31 DemProx vs fixed 0.6 =>0.985 and 0.89

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

    def save_results(self):
        root_train = np.asarray(self.gs_level_train)[K_Levels,:, 0]
        root_test = np.asarray(self.gs_level_test)[K_Levels,:, 0]

        write_file(file_name=rs_file_path, root_test=root_test, root_train=root_train,
                   cs_avg_data_test=self.cs_avg_data_test, cs_avg_data_train=self.cs_avg_data_train,
                   cg_avg_data_test=self.cg_avg_data_test, cg_avg_data_train=self.cg_avg_data_train,
                   cs_data_test=self.cs_data_test, cs_data_train=self.cs_data_train, cg_data_test=self.cg_data_test,
                   cg_data_train=self.cg_data_train, gs_level_train=self.gs_level_train, gs_level_test=self.gs_level_test,
                   gg_level_train = self.gg_level_train, gg_level_test = self.gg_level_test,
                   gks_level_train =self.gks_level_train , gks_level_test=self.gks_level_test,
                   gkg_level_train=self.gkg_level_train, gkg_level_test=self.gkg_level_test,
                   dendo_data=self.dendo_data, dendo_data_round=self.dendo_data_round,  #Dendrogram data
                   N_clients=[N_clients], TREE_UPDATE_PERIOD=[TREE_UPDATE_PERIOD])      #Setting
        plot_from_file()

