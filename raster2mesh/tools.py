
def mpl_plot_mesh(mesh, mask=None):
    from matplotlib import pyplot as plt

    V = mesh.points

    fig, ax = plt.subplots(1+ (mask!=None) )
    img = ax[0].scatter(V[:,0], V[:,1], c=V[:,2], cmap=plt.hot())
    if mask != None:
        img2 = ax[1].scatter(V[mask,0], V[mask,1], c=V[mask,2], cmap=plt.viridis())

    fig.colorbar(img)

    ax[0].set_xlabel('X')
    ax[0].set_ylabel('Y')

    plt.show()