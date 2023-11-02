import numpy as np
import os, sys
import time
from numba import njit
import cubature

from param import *
from mathematica import *


############################################################################# integrand for Cl
@njit
def theintegrand(rvar, chi, nu_p, ell, r_list, f_of_r):
    result = np.zeros((len(rvar), 2), dtype=np.float64)
    tvar=rvar/chi

    if ell>=5: t1min = tmin_fct(ell, nu_p)
    else: t1min=0
    
    for ind, t in enumerate(tvar[:,0]):

        res=myhyp21(nu_p, t, chi, ell, t1min) * np.interp(rvar[ind,0], r_list, f_of_r)
        result[ind] = [res.real, res.imag]
    return result 

@njit
def theintegrand_sum(rvar, chi, ell, n, r_list, f_of_rp, N, kmax, kmin, kpow, b):
    res = np.zeros((len(rvar[:,0])), dtype=np.complex128)
    for p in range(-N//2, N//2+1):
        eta_p = 2.*np.pi*p/np.log(kmax/kmin)
        nu_p = 1.+b+n+1j*eta_p + kpow
    
        val = theintegrand(rvar, chi, nu_p, ell, r_list, f_of_rp[p+N//2])
        res+=val[:,0]+val[:,1]*1j
    return res.real

@njit
def theintegrand_sum_quadratic(rvar, chi, ell, n, r_list, f_of_rp, N, kmax, kmin, kpow, b_list):
    res = np.zeros((len(rvar[:,0])), dtype=np.float64)
    for ind, b in enumerate(b_list):
        res+=theintegrand_sum(rvar, chi, ell, n, r_list, f_of_rp[:,:,ind], N, kmax, kmin, kpow, b)

    return res


def get_Cl_sum(integrand, chi, ell, n, r_list, y, y1, rmin, rmax, N, kmax, kmin, kpow, b):
    print('  n={}'.format(n))
    if n==2:
        f_of_rp=y1
        n-=2
    else:
        f_of_rp=y

    val, err = cubature.cubature(integrand, ndim=1, fdim=1, xmin=[rmin], xmax=[rmax],\
                                     args=(chi, ell, n, r_list, f_of_rp, N, kmax, kmin, kpow, b), \
                                     relerr=relerr, maxEval=1e5, abserr=0, vectorized=True)
    return val/4./np.pi

def get_all_Cln(which, qterm, lterm, chi_list, ell, r_list, y, y1, rmin, rmax, N, kmax, kmin, kpow, b):
    print(' C_ell={}'.format(int(ell)))

    if gauge=='new' and lterm!='pot':
        stuff2=(2./3./omega_m/H0**2)**2
    elif lterm=='pot':
        stuff2=(2./3./omega_m/H0**2)
    else:
        stuff2=1.

    if which=='FG2':
        res=np.zeros((len(chi_list), 4))
        cl_name = output_dir+'Cln_{}_ell{}.txt'.format(lterm, int(ell))
        integrand=theintegrand_sum
    else:
        if qterm==0:
            res=np.zeros((len(chi_list), 2))
            cl_name = output_dir+'Cln_{}_{}_ell{}.txt'.format(which, lterm, int(ell))
            integrand=theintegrand_sum_quadratic
        else:
            res=np.zeros((len(chi_list), 2))
            cl_name = output_dir+'Cln_{}_qterm{}_{}_ell{}.txt'.format(which, qterm, lterm, int(ell))
            integrand=theintegrand_sum

    print(' ') 
    print('integration {}'.format(cl_name)) 
    #if #not os.path.isfile(cl_name) or force:
    if os.path.isfile(cl_name):
        res=np.loadtxt(cl_name)
    else:
        res[:,0]=chi_list

    a=time.time()
    for ind, chi in enumerate(chi_list):
        if ind%1==0: 
            print('  {}/{} chi={:.2f}, time {:.2f}'.format(ind, len(chi_list), chi, time.time()-a))

        if res[ind,1]!=0: 
            print('     already computed -> jump')
            continue
        res[ind,1]=stuff2*get_Cl_sum(integrand, chi, ell, 0, r_list, y, None, rmin, rmax, N, kmax, kmin, kpow, b)

        if which=='FG2':
            if res[ind,2]!=0: 
                print('     already computed -> jump')
                continue
            res[ind,2]=stuff2*get_Cl_sum(integrand, chi, ell, -2, r_list, y, y1, rmin, rmax, N, kmax, kmin, kpow, b)

            if res[ind,3]!=0: 
                print('     already computed -> jump')
                continue
            res[ind,3]=stuff2*get_Cl_sum(integrand, chi, ell, 2, r_list, y, y1, rmin, rmax, N, kmax, kmin, kpow, b)
        
        np.savetxt(cl_name, res) 
    else:
        res=np.loadtxt(cl_name)
    return res




#def Cl_driver():
#         y[:,:,ind]=get_cp_of_r(r_list, tr['k'], Pk, gauge, lt, which, qt, False, ra, a, Ha, D, f, r0, ddr, normW, b_list[ind])
#         np.save('cp_of_r', y)
#
#         for ell in np.float64(argv[ell_start:]):
#             if len(qterm_list)==1:
#                 y1=mathcalD(r_list, y[:,:,ind], ell)
#                 get_all_Cln(which, qt, lt, chi_list, ell, r_list, y[:,:,0], y1, rmin, rmax, len(tr['k']), kmax, kmin, kpow, b_list[0])
#             elif compute_all_separate:
#                 y1=mathcalD(r_list, y[:,:,ind], ell)
#                 get_all_Cln(which, qt, lt, chi_list, ell, r_list, y[:,:,ind], y1, rmin, rmax, len(tr['k']), kmax, kmin, kpow, b_list[ind])
#             else:
#                 compute_all=True
#
#     if compute_all:
#                for ell in np.float64(argv[ell_start:]):
#                    get_all_Cln(which, qterm, lt, chi_list, ell, r_list, y, 0, rmin, rmax, len(tr['k']), kmax, kmin, kpow, b_list)


def plot_integrand(ell, n, r_list, y, y1, rmin, rmax, N, kmax, kmin, kpow, b):
    rvar_list=np.linspace(rmin, rmax, 1000)
    chi = (rmin+rmax)/2.
    a=time.time()
    res = theintegrand_sum(rvar_list[:,None], chi, ell, n, r_list, y, N, kmax, kmin, kpow, b)
    np.savetxt('integrand.txt', np.array([rvar_list, res]).T)
    print(time.time()-a)




























