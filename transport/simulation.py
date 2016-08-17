# coding: utf-8
import random,math



ENDTIME = 1.0  #end of time
TIMESTEP = 0.005 #interval of output
OUTFILE = 'out.dat' #output file
PLTFILE = 'out.plt' #gnuplot script file
PNGFILE = 'out.png' #png file
SEED = 123 #random seed
N = 1 #number of reaction
M = 2 #number of chemical species

x = [0,0]  #population of chemical species
c = [0.0]  #reaction rates
p = [0.0]  #propencities of reaction
u1 = [0,0]  #data structure for updating x[]
u2 = [0,0]  #data structure for updating x[]

# X0 + X1 -- c0 --> X1 + X1

def init(x,c,u1,u2):
    #population of chemical species
    #x[0] = 1000
    #x[1] = 500

    #reaction rates
    c[0] = 0.1

    #data structure for updating the number of chemical species
    #u1[i][j]: i=reaction number, j=chemical species
    #each element is corresponding to the element of u2 array
    #u1[0][0] = 0
    #u1[0][1] = 1

    #u2[i][j]: i=reaction number, j=in(de)crement of chemical species
    #u2[0][0] = -1
    #u2[0][1] = 1

# function for updating the reaction propencities
def update_p(p,c,x):
    p[0] = c[0]*x[0]*x[1]  # x0 + x1 -> x1 + x1

#functions
def select_reaction(p,pn,sum_propencity,r):
    reaction = -1
    sp = 0.0
    r = r * sum_propencity
    for i in range(pn):
        sp += p[i]
        if(r < sp):
            reaction = i
            break
    return reaction


def update_x(x,u1,u2,reaction):
    for i in range(2):
        x[u1[reaction][i]] += u2[reaction][i]


def output(out,t,x,xn):
    output_t = 0.0
    if(output_t <= t):
        out.write('%f' % t)
        for i in range(xn):
            out.write('\t%d' % x[i])
        out.write('\n')
        output_t += TIMESTEP


def output_gnuplot(n):
    out = open(PLTFILE,'w')
    outfile = OUTFILE
    pngfile = PNGFILE

    out.write('set xlabel \"Time\"\n')
    out.write('set ylabel \"Number of Chemical Species\"\n')
    out.write('p ')
    for i in range(n):
        if(i > 0):
            out.write(',')
        out.write("\"%s\" u 1:%d t \"X%d\" w l" % (outfile, i+2, i))
    out.write('\n')
    out.write('set term png\n')
    out.write('set out \"%s\"\n' % (pngfile))
    out.write('rep\n')
    out.write('pause -1 \'Enter\'\n')

    print('Type the following command if gnuplot is installed in your computer.')
    print('>gnuplot %s\n' % (pngfile))

    out.close()



def sum(a,n):
    s = 0.0
    for i in range(n):
        s += a[i]
    return s


if __name__ == '__main__':
    sum_propencity = 0.0
    tau = 0.0
    t = 0.0
    init(x,c,u1,u2)

    random.seed(SEED)
    out = open(OUTFILE,'w')

    #main loop
    while(True):
        #output
        #output(out,t,x,M)

        #update propencity
        #update_p(p,c,x)
        #sum_propencity = sum(p,N)




        #sample tau
        if(sum_propencity > 0):
            tau = -math.log(random.random())/sum_propencity
        else:
            break

        #select reaction
        r = random.random()
        reaction = select_reaction(p,N,sum_propencity,r)

        # update chemical species
        update_x(x,u1,u2,reaction)

        # time
        t += tau

    out.close()
    output_gnuplot(M)