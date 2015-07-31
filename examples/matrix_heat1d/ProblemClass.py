from __future__ import division
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as LA

from pySDC.Problem import ptype
from pySDC.datatype_classes.mesh import mesh, rhs_imex_mesh
from pySDC.tools.transfer_tools import to_sparse

class heat1d(ptype):
    """
    Example implementing the forced 1D heat equation with Dirichlet-0 BC in [0,1]

    Attributes:
        A: second-order FD discretization of the 1D laplace operator
        dx: distance between two spatial nodes
    """

    def __init__(self, cparams, dtype_u, dtype_f):
        """
        Initialization routine

        Args:
            cparams: custom parameters for the example
            dtype_u: temperature on a mesh (will be passed parent class)
            dtype_f: temperature per time unit on a mesh (will be passed parent class)
        """

        # these parameters will be used later, so assert their existence
        assert 'nvars' in cparams
        assert 'nu' in cparams

        # add parameters as attributes for further reference
        for k,v in cparams.items():
            setattr(self,k,v)

        # invoke super init, passing number of dofs, dtype_u and dtype_f
        super(heat1d,self).__init__(self.nvars,dtype_u,dtype_f)

        # compute dx and get discretization matrix A
        self.dx = 1/(self.nvars + 1)
        self.A = self.__get_A(self.nvars,self.nu,self.dx)
        self.xvalues = np.array([(i+1)*self.dx for i in range(self.nvars)])

    def __get_A(self,N,nu,dx):
        """
        Helper function to assemble FD matrix A in sparse format

        Args:
            N: number of dofs
            nu: diffusion coefficient
            dx: distance between two spatial nodes

        Returns:
         matrix A in CSC format
        """

        stencil = [1, -2, 1]
        A = sp.diags(stencil,[-1,0,1],shape=(N,N))
        A *= nu / (dx**2)
        return A.tocsc()


    def solve_system(self,rhs,factor,u0):
        """
        Simple linear solver for (I-dtA)u = rhs

        Args:
            rhs: right-hand side for the nonlinear system
            factor: abbrev. for the node-to-node stepsize (or any other factor required)
            u0: initial guess for the iterative solver (not used here so far)

        Returns:
            solution as mesh
        """

        me = mesh(self.nvars)
        # me.values = LA.spsolve(sp.eye(self.nvars)-factor*self.A,rhs.values)
        Minv = LA.inv(sp.eye(self.nvars)-factor*self.A)
        me.values = Minv.dot(rhs.values)
        return me


    def __eval_fexpl(self,u,t):
        """
        Helper routine to evaluate the explicit part of the RHS

        Args:
            u: current values (not used here)
            t: current time

        Returns:
            explicit part of RHS
        """

        xvalues = np.array([(i+1)*self.dx for i in range(self.nvars)])
        fexpl = mesh(self.nvars)
        # fexpl.values = -np.sin(np.pi*xvalues)*(np.sin(t)-self.nu*np.pi**2*np.cos(t))
        fexpl.values = np.zeros(self.nvars)
        return fexpl

    def __eval_fimpl(self,u,t):
        """
        Helper routine to evaluate the implicit part of the RHS

        Args:
            u: current values
            t: current time (not used here)

        Returns:
            implicit part of RHS
        """

        fimpl = mesh(self.nvars)
        fimpl.values = self.A.dot(u.values)
        return fimpl


    def eval_f(self,u,t):
        """
        Routine to evaluate both parts of the RHS

        Args:
            u: current values
            t: current time

        Returns:
            the RHS divided into two parts
        """

        f = rhs_imex_mesh(self.nvars)
        f.impl = self.__eval_fimpl(u,t)
        f.expl = self.__eval_fexpl(u,t)
        return f


    def u_exact(self,t):
        """
        Routine to compute the exact solution at time t

        Args:
            t: current time

        Returns:
            exact solution
        """

        me = mesh(self.nvars)
        # xvalues = np.array([(i+1)*self.dx for i in range(self.nvars)])
        # me.values = np.sin(np.pi*self.xvalues)*np.cos(t)
        me.values = np.sin(np.pi*self.xvalues)*np.exp(-np.pi**2 * self.nu * t)
        return me


    def get_mesh(self, form="list"):
        """
        Returns the mesh the problem is computed on.

        :param form: the form in which the mesh is needed
        :return: depends on form
        """

        if form is "list":
            return [np.linspace(0, 1, self.nvars)]
        elif form is "meshgrid":
            return np.linspace(0, 1, self.nvars)
        else:
            return None


    @property
    def system_matrix(self):
        """
        Returns the system matrix
        :return:
        """
        return self.A

    @property
    def A_I(self):
        return self.A

    @property
    def A_E(self):
        return np.zeros(self.A.shape)

    def force_term(self, t):
        """
        For the linear matrix framework it is possible to
        deal with forcing terms as long they only depend on t.
        :param t: time point , array
        :return: forcing term of the heat  equation
        """
        if type(t) is np.ndarray:
            return np.zeros(self.xvalues.shape[0]*t.shape[0])
            # return np.hstack(map(lambda tau: -np.sin(np.pi*self.xvalues)*(np.sin(tau)-self.nu*np.pi**2*np.cos(tau)), t))
        else:
            return -np.sin(np.pi*self.xvalues)*(np.sin(t)-self.nu*np.pi**2*np.cos(t))

# TODO change to periodic heat1d problem.

class heat1d_periodic(ptype):
    """
    Example implementing the forced 1D heat equation with periodic boundaries
    Attributes:
        A: second-order FD discretization of the 1D laplace operator
        dx: distance between two spatial nodes
    """

    def __init__(self, cparams, dtype_u, dtype_f):
        """
        Initialization routine

        Args:
            cparams: custom parameters for the example
            dtype_u: temperature on a mesh (will be passed parent class)
            dtype_f: temperature per time unit on a mesh (will be passed parent class)
        """

        # these parameters will be used later, so assert their existence
        assert 'nvars' in cparams
        assert 'nu' in cparams
        
        if 'sparse_format' in cparams:
            self.sparse_format = cparams['sparse_format']
        else:
            self.sparse_format = "array"

        # add parameters as attributes for further reference
        for k,v in cparams.items():
            setattr(self,k,v)

        # invoke super init, passing number of dofs, dtype_u and dtype_f
        super(heat1d_periodic,self).__init__(self.nvars,dtype_u,dtype_f)

        # compute dx and get discretization matrix A
        self.dx = 1.0/self.nvars 
        self.A = self.__get_A(self.nvars,self.nu,self.dx)
        self.xvalues = np.array([i*self.dx for i in range(self.nvars)])
        

    def __get_A(self,N,nu,dx):
        """
        Helper function to assemble FD matrix A in sparse format

        Args:
            N: number of dofs
            nu: diffusion coefficient
            dx: distance between two spatial nodes

        Returns:
         matrix A in CSC format
        """

        stencil = [1, -2, 1]
        A = sp.diags(stencil,[-1,0,1],shape=(N,N))+sp.diags([[1.0],[1.0]],[N-1,1-N])
        A *= nu / (dx**2)
        return to_sparse(A, self.sparse_format)


    def solve_system(self,rhs,factor,u0):
        """
        Simple linear solver for (I-dtA)u = rhs

        Args:
            rhs: right-hand side for the nonlinear system
            factor: abbrev. for the node-to-node stepsize (or any other factor required)
            u0: initial guess for the iterative solver (not used here so far)

        Returns:
            solution as mesh
        """

        me = mesh(self.nvars)
        # me.values = LA.spsolve(sp.eye(self.nvars)-factor*self.A,rhs.values)
        Minv = LA.inv(sp.eye(self.nvars)-factor*self.A)
        me.values = Minv.dot(rhs.values)
        return me


    def __eval_fexpl(self,u,t):
        """
        Helper routine to evaluate the explicit part of the RHS

        Args:
            u: current values (not used here)
            t: current time

        Returns:
            explicit part of RHS
        """

        xvalues = np.array([i*self.dx for i in range(self.nvars)])
        fexpl = mesh(self.nvars)
        # fexpl.values = -np.sin(np.pi*xvalues)*(np.sin(t)-self.nu*np.pi**2*np.cos(t))
        fexpl.values = np.zeros(self.nvars)
        return fexpl

    def __eval_fimpl(self,u,t):
        """
        Helper routine to evaluate the implicit part of the RHS

        Args:
            u: current values
            t: current time (not used here)

        Returns:
            implicit part of RHS
        """

        fimpl = mesh(self.nvars)
        fimpl.values = self.A.dot(u.values)
        return fimpl


    def eval_f(self,u,t):
        """
        Routine to evaluate both parts of the RHS

        Args:
            u: current values
            t: current time

        Returns:
            the RHS divided into two parts
        """

        f = rhs_imex_mesh(self.nvars)
        f.impl = self.__eval_fimpl(u,t)
        f.expl = self.__eval_fexpl(u,t)
        return f


    def u_exact(self,t):
        """
        Routine to compute the exact solution at time t

        Args:
            t: current time

        Returns:
            exact solution
        """

        me = mesh(self.nvars)
        # xvalues = np.array([(i+1)*self.dx for i in range(self.nvars)])
        # me.values = np.sin(np.pi*self.xvalues)*np.cos(t)
        me.values = np.sin(np.pi*self.xvalues)*np.exp(-np.pi**2 * self.nu * t)
        return me


    def get_mesh(self, form="list"):
        """
        Returns the mesh the problem is computed on.

        :param form: the form in which the mesh is needed
        :return: depends on form
        """

        if form is "list":
            return [np.linspace(0, 1.0-1.0/self.nvars, self.nvars)]
        elif form is "meshgrid":
            return np.linspace(0, 1.0-1.0/self.nvars, self.nvars)
        else:
            return None


    @property
    def system_matrix(self):
        """
        Returns the system matrix
        :return:
        """
        return self.A

    @property
    def A_I(self):
        return self.A

    @property
    def A_E(self):
        return np.zeros(self.A.shape)

    def force_term(self, t):
        """
        For the linear matrix framework it is possible to
        deal with forcing terms as long they only depend on t.
        :param t: time point , array
        :return: forcing term of the heat  equation
        """
        if type(t) is np.ndarray:
            return np.zeros(self.xvalues.shape[0]*t.shape[0])
            # return np.hstack(map(lambda tau: -np.sin(np.pi*self.xvalues)*(np.sin(tau)-self.nu*np.pi**2*np.cos(tau)), t))
        else:
            return -np.sin(np.pi*self.xvalues)*(np.sin(t)-self.nu*np.pi**2*np.cos(t))

