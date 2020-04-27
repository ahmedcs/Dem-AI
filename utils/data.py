import h5py as hf
import numpy as np
from clustering.Setting import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def  write_file(file_name = "../results/untitled.h5", **kwargs):
    with hf.File(file_name, "w") as data_file:
        for key, value in kwargs.items():
            #print("%s == %s" % (key, value))
            data_file.create_dataset(key, data=value)
    print("Successfully save to file!")
def read_data(file_name = "../results/untitled.h5"):
    rs = []
    dic_data = {}
    with hf.File(file_name, "r") as f:
        # List all groups
        #print("Keys: %s" % f.keys())
        for key in f.keys():
            rs.append( [key, f[key][:]] )
            dic_data[key] = f[key][:]
    return   dic_data
def plot_from_file():
    file_name = "../results/alg_{}_iter_{}_k_{}_w.h5".format(RUNNING_ALG, NUM_GLOBAL_ITERS, K_Levels)
    f_data = read_data( file_name )
    print("DEM-AI --------->>>>> Plotting")
    alg_name = RUNNING_ALG + "_"

    plt.figure(3)
    plt.clf()
    plt.plot(f_data['root_train'], label="Root_train", linestyle="--")
    plt.plot(f_data['root_test'], label="Root_test", linestyle="--")
    plt.plot(np.arange(len(f_data['cs_avg_data_train'])), f_data['cs_avg_data_train'], linestyle="-",
             label="Client_spec_train")
    plt.plot(np.arange(len(f_data['cs_avg_data_test'])), f_data['cs_avg_data_test'], linestyle="-", label="Client_spec_test")
    plt.plot(np.arange(len(f_data['cg_avg_data_train'])), f_data['cg_avg_data_train'], linestyle="-",
             label="Client_gen_train")
    plt.plot(np.arange(len(f_data['cg_avg_data_test'])), f_data['cg_avg_data_test'], linestyle="-", label="Client_gen_test")
    plt.legend()
    plt.xlabel("Global Rounds")
    plt.ylim(0, 1.02)
    plt.grid()
    plt.title("AVG Clients Model (Spec-Gen) Accuracy")
    plt.savefig(PLOT_PATH + alg_name + "AVGC_Spec_Gen.pdf")

    # plt.figure(3)
    # plt.clf()
    # plt.plot(root_train, label="Root_train", linestyle="--")
    # plt.plot(np.arange(len(f_data['cs_avg_data_train'])), f_data['cs_avg_data_train'], label="Client_spec_train")
    # plt.plot(np.arange(len(f_data['cg_avg_data_train'])), f_data['cg_avg_data_train'], label="Client_gen_train")
    # plt.legend()
    # plt.xlabel("Global Rounds")
    # plt.ylim(0, 1.02)
    # plt.grid()
    # plt.title("AVG Clients Model (Spec-Gen) Training Accuracy")
    # plt.savefig(PLOT_PATH + alg_name+"AVGC_Spec_Gen_Training.pdf")
    #
    # plt.figure(4)
    # plt.clf()
    # plt.plot(root_test, label="Root_test", linestyle="--")
    # plt.plot(np.arange(len(f_data['cs_avg_data_test'])), f_data['cs_avg_data_test'], label="Client_spec_test")
    # plt.plot(np.arange(len(f_data['cg_avg_data_test'])), f_data['cg_avg_data_test'], label="Client_gen_test")
    # plt.legend()
    # plt.xlabel("Global Rounds")
    # plt.ylim(0, 1.02)
    # plt.grid()
    # plt.title("AVG Clients Model (Spec-Gen) Testing Accuracy")
    # plt.savefig(PLOT_PATH + alg_name+"AVGC_Spec_Gen_Testing.pdf")

    # plt.figure(5)
    # plt.clf()
    # plt.plot(np.arange(len(self.gs_data_train)), self.gs_data_train, label="s_train")
    # plt.plot(np.arange(len(self.gs_data_test)), self.gs_data_test, label="s_test")
    # # print(self.gs_data_test)

    # plt.legend()
    # plt.grid()
    # plt.title("AVG Group Specialization")

    # plt.figure(6)
    # plt.clf()
    # plt.plot(np.arange(len(self.gg_data_train)), self.gg_data_train, label="g_train")
    # plt.plot(np.arange(len(self.gg_data_test)), self.gg_data_test, label="g_test")
    # plt.legend()
    # plt.grid()
    # plt.title("AVG Group Generalization")

    plt.figure(7)
    plt.clf()
    plt.plot(f_data['root_test'], linestyle="--", label="root test")
    plt.plot(f_data['cs_data_test'])
    plt.legend()
    plt.xlabel("Global Rounds")
    plt.ylim(0, 1.02)
    plt.grid()
    plt.title("Testing Client Specialization")
    plt.savefig(PLOT_PATH + alg_name + "C_Spec_Testing.pdf")

    plt.figure(8)
    plt.clf()
    plt.plot(f_data['root_train'], linestyle="--", label="root train")
    plt.plot(f_data['cs_data_train'])
    plt.legend()
    plt.xlabel("Global Rounds")
    plt.ylim(0, 1.02)
    plt.grid()
    plt.title("Training Client Specialization")
    plt.savefig(PLOT_PATH + alg_name + "C_Spec_Training.pdf")

    plt.figure(9)
    plt.clf()
    plt.plot(f_data['cg_data_test'])
    plt.plot(f_data['root_test'], linestyle="--", label="root test")
    plt.legend()
    plt.xlabel("Global Rounds")
    plt.ylim(0, 1.02)
    plt.grid()
    plt.title("Testing Client Generalization")
    plt.savefig(PLOT_PATH + alg_name + "C_Gen_Testing.pdf")

    plt.figure(10)
    plt.clf()
    plt.plot(f_data['cg_data_train'])
    plt.plot(f_data['root_train'], linestyle="--", label="root train")
    plt.legend()
    plt.xlabel("Global Rounds")
    plt.ylim(0, 1.02)
    plt.grid()
    plt.title("Training Client Generalization")
    plt.savefig(PLOT_PATH + alg_name + "C_Gen_Training.pdf")

    plt.show()

    print("** Summary Results: ---- Training ----")
    print("AVG Clients Specialization - Training:", f_data['cs_avg_data_train'])
    print("AVG Clients Generalization - Training::", f_data['cg_avg_data_train'])
    print("Root performance - Training:", f_data['root_train'])
    print("** Summary Results: ---- Testing ----")
    print("AVG Clients Specialization - Testing:", f_data['cs_avg_data_test'])
    print("AVG Clients Generalization - Testing:", f_data['cg_avg_data_test'])
    print("Root performance - Testing:", f_data['root_test'])

def plot_3D():
    file_name = "../results/alg_{}_iter_{}_k_{}_w.h5".format(RUNNING_ALG, NUM_GLOBAL_ITERS, K_Levels)
    f_data = read_data(file_name)
    data = np.array(f_data['g_level_test'])

    lx = len(data[0])
    print(lx)
    # Work out matrix dimensions
    ly = len(data[:, 0])
    print(ly)

    column_names = np.arange(lx)
    row_names = np.arange(ly)

    fig = plt.figure()
    ax = Axes3D(fig)

    xpos = np.arange(0, lx, 1)  # Set up a mesh of positions
    ypos = np.arange(0, ly, 1)
    xpos, ypos = np.meshgrid(xpos + 0.25, ypos + 0.25)

    xpos = xpos.flatten()  # Convert positions to 1D array
    ypos = ypos.flatten()
    zpos = np.zeros(lx * ly)

    dx = 0.5 * np.ones_like(zpos)
    dy = dx.copy()
    dz = data.flatten()

    # cs = ['r', 'g', 'b', 'y', 'c'] * ly

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz)

    # sh()
    # ax.w_xaxis.set_ticklabels(column_names)
    # ax.w_yaxis.set_ticklabels(row_names)

    plt.show()

if __name__=='__main__':
    # a = [[0.09540889526542325, 0.1135953840605842], [0.9921090387374462, 0.998918139199423], [0.9921090387374462, 0.999278759466282], [0.994261119081779, 1.0], [0.9928263988522238, 1.0], [0.9928263988522238, 1.0], [0.9921090387374462, 1.0], [0.9921090387374462, 1.0], [0.9921090387374462, 1.0], [0.9921090387374462, 1.0]]
    # b = np.asarray(a)
    # c = np.asarray([1,2,3,4,5,6,7,8])
    # write_file( file_name="../results/tri_test.h5", b=b, c=c)
    file_name = "../results/alg_{}_iter_{}_k_{}_w.h5".format(RUNNING_ALG, NUM_GLOBAL_ITERS, K_Levels)
    dt = read_data(file_name)
    print(dt)
    plot_3D()
    # print(dt['cs_avg_data_test'])
    # print(dt['cs_avg_data_train'])
    # print(dt['root_test'])
    # print(dt['root_train'])
    plot_from_file()