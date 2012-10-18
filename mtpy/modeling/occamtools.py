# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 11:54:38 2011

@author: a1185872
"""

import numpy as np
import scipy as sp
import os
import fnmatch
from operator import itemgetter
import time
import matplotlib.colorbar as mcb
from matplotlib.colors import Normalize
from matplotlib.ticker import MultipleLocator
import matplotlib.gridspec as gridspec
import mtply.core.z as Z
import mtply.modeling.winglinktools as wlt
import matplotlib.pyplot as plt


occamdict={'1':'resxy','2':'phasexy','3':'realtip','4':'imagtip','5':'resyx',
           '6':'phaseyx'}

class Occam1D:
    """
    ==============================================
    This class will deal with everything occam 1D
    =============================================
    """
    
    def __init__(self,datafn_te=None,datafn_tm=None):
                     
        self.datafn_te=datafn_te
        self.datafn_tm=datafn_tm
        self.modelfn=None
        self.inputfn=None
        
        if self.datafn_te:
            self.dirpath=os.path.dirname(self.datafn_te)
        elif self.datafn_tm:
            self.dirpath=os.path.dirname(self.datafn_tm)
        elif self.iterfn_te:
            self.dirpath=os.path.dirname(self.iterfn_te)
        elif self.iterfn_tm:
            self.dirpath=os.path.dirname(self.iterfn_tm)
        else:
            self.dirpath=None
            
    def make1DdataFile(self,station,edipath=None,savepath=None,
                       polarization='both',reserr='data',phaseerr='data',
                       fmt='%+.6e',ss=3*' ',thetar=0):
        """
        make1Ddatafile will write a data file for Occam1D
    
        Arguments:
        ---------    
            **station** : the station name and path if edipath=None
            
            **edipath** : path to the edi files to be written into a data file,
                          useful for multile data files
                      
            **savepath** : path to save the file, if None set to dirname of 
                           station if edipath = None.  Otherwise set to 
                           dirname of edipath.
            
            **thetar** : rotation angle to rotate Z. Clockwise positive and N=0
                         *default* = 0
            
            **polarization** : polarization to model can be (*default*='both'):
                
                                -'both' for TE and TM as separate files,
                                
                                -'TE' for just TE mode
                                
                                -'TM' for just TM mode
                            
            **reserr** : errorbar for resistivity values.  Can be set to (
                        *default* = 'data'): 
                
                        -'data' for errorbars from the data
                        
                        -percent number ex. 10 for ten percent
                    
            **phaseerr** : errorbar for phase values.  Can be set to (
                         *default* = 'data'):
                
                            -'data' for errorbars from the data
                            
                            -percent number ex. 10 for ten percent
                        
            **fmt** : format of the values written to the file. 
                      *default* = %+.6e
            
            **ss** : spacing between values in file.  *default* = ' '*3
            
            Returns:
            --------
                **datafn_te** : full path to data file for TE mode
                
                **datafn_tm** : full path to data file for TM mode
                
            
            """    
    
        if os.path.dirname(station)=='':
            if edipath==None:
                raise IOError('Need to input a path for the file.')
            else:
                #find the edifile
                for fn in os.listdir(edipath):
                    if fn.lower().find(station.lower())>=0:
                        edifile=os.path.join(edipath,fn)
        else:
            edifile=station
                
        #raise an error if can't find the edifile        
        if edifile==None:
            raise NameError('No edifile exists, check path and station name')
    
        #read in edifile    
        impz=Z.Z(edifile)    
        
        #make sure the savepath exists, if not create it
        if savepath==None:
            savepath=os.path.dirname(edifile)
            if not os.path.exists(savepath):
                os.mkdir(savepath)
        if os.path.basename(savepath).find('.')>0:
            savepath=os.path.dirname(savepath)
            if not os.path.exists(savepath):
                os.mkdir(os.path.dirname(savepath))
        else:
            savepath=savepath
            if not os.path.exists(savepath):
                os.mkdir(os.path.dirname(savepath))
                
        
        #load the edifile and get resistivity and phase
        rp=impz.getResPhase(thetar=thetar)
        freq=impz.frequency
        nf=len(freq)
        returnfn=[]
        
        if polarization=='both':
            for pol in ['xy','yx']:
                if pol=='xy':
                    dfilesave=os.path.join(savepath,impz.station+'TE.dat')
                elif pol=='yx':
                    dfilesave=os.path.join(savepath,impz.station+'TM.dat')
    
                datafid=open(dfilesave,'w')
    
                datafid.write('Format:  EMData_1.1 \n')
                datafid.write('!Polarization:'+ss+pol+'\n')
    
                #needs a transmitter to work so put in a dummy one
                datafid.write('# Transmitters: 1\n')
                datafid.write('0 0 0 0 0 \n')
                
                #write frequencies
                datafid.write('# Frequencies:'+ss+str(nf)+'\n')       
                for ff in freq:
                    datafid.write(ss+'%.6f' % ff+'\n')
                
                #needs a receiver to work so put in a dummy one
                datafid.write('# Receivers: 1 \n')
                datafid.write('0 0 0 0 0 0 \n')
                
                #write data
                datafid.write('# Data:'+2*ss+str(2*nf)+'\n')
                datafid.write('!'+2*ss+'Type'+2*ss+'Freq#'+2*ss+'Tx#'+2*ss+
                             'Rx#'+ 2*ss+'Data'+2*ss+'Std_Error'+'\n')
                              
                #put the yx phase component in the first quadrant as prescribed
                if pol=='yx':
                        rp.phaseyx=rp.phaseyx+180
                        #check if there are any negative phases
                        negphase=np.where(rp.phaseyx>180)
                        if len(negphase)>0:
                            rp.phaseyx[negphase[0]]=rp.phaseyx\
                                                            [negphase[0]]-360
                        
                #write the resistivity and phase components
                for ii in range(nf):
                    #write resistivity components
                    if reserr=='data':
                        if pol=='xy':
                            datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.resxy[ii]+2*ss+
                                          fmt % rp.resxyerr[ii]+'\n')
                        elif pol=='yx':
                            datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.resyx[ii]+2*ss+
                                          fmt % rp.resyxerr[ii]+'\n')
                    else:
                        if pol=='xy':
                            datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.resxy[ii]+2*ss+
                                          fmt % (rp.resxy[ii]*reserr/100.)+'\n')
                        elif pol=='yx':
                            datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.resyx[ii]+2*ss+
                                          fmt % (rp.resyx[ii]*reserr/100.)+'\n')
                    
                    #write phase components
                    if phaseerr=='data':
                        if pol=='xy':
                            datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.phasexy[ii]+2*ss+
                                          fmt % rp.phasexyerr[ii]+'\n')
                        if pol=='yx':
                            datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.phaseyx[ii]+2*ss+
                                          fmt % rp.phaseyxerr[ii]+'\n')
                    else:
                        if pol=='xy':
                            datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.phasexy[ii]+2*ss+
                                          fmt % (phaseerr/100.*(180/np.pi))+'\n')
                        if pol=='yx':
                            datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                          2*ss+'1'+2*ss+fmt % rp.phaseyx[ii]+2*ss+
                                          fmt % (phaseerr/100.*(180/np.pi))+'\n')
                datafid.write('\n')
                datafid.close()
                print 'Wrote Data File: ',dfilesave
                returnfn.append(dfilesave)
            self.datafn_te=returnfn[0]
            self.datafn_tm=returnfn[1]
        else:
            if polarization=='TE':
                pol='xy'
                dfilesave=os.path.join(savepath,impz.station+'TE.dat')
                self.datafn_te=dfilesave
            elif polarization=='TM':
                pol='yx'
                dfilesave=os.path.join(savepath,impz.station+'TM.dat')
                self.datafn_te=dfilesave
                
            
            
    
            #open file to write to
            datafid=open(dfilesave,'w')
            datafid.write('Format:  EMData_1.1 \n')
            datafid.write('!Polarization:'+ss+pol+'\n')
    
            #needs a transmitter to work so put in a dummy one
            datafid.write('# Transmitters: 1\n')
            datafid.write('0 0 0 0 0 \n')
            
            #write frequencies
            datafid.write('# Frequencies:'+ss+str(nf)+'\n')       
            for ff in freq:
                datafid.write(ss+'%.6f' % ff+'\n')
            
            #needs a receiver to work so put in a dummy one
            datafid.write('# Receivers: 1 \n')
            datafid.write('0 0 0 0 0 0 \n')
            
            #write header line
            datafid.write('# Data:'+2*ss+str(2*nf)+'\n')
            datafid.write('!'+2*ss+'Type'+2*ss+'Freq#'+2*ss+'Tx#'+2*ss+'Rx#'+
                          2*ss+'Data'+2*ss+'Std_Error'+'\n')
                          
            #put the yx phase component in the first quadrant as prescribed
            if pol=='yx':
                    rp.phaseyx=rp.phaseyx+180
                    #check if there are any negative phases
                    negphase=np.where(rp.phaseyx>180)
                    if len(negphase)>0:
                        rp.phaseyx[negphase[0]]=rp.phaseyx\
                                                        [negphase[0]]-360
                    
            #write the resistivity and phase components
            for ii in range(nf):
                #write resistivity components
                if reserr=='data':
                    if pol=='xy':
                        datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.resxy[ii]+2*ss+
                                      fmt % rp.resxyerr[ii]+'\n')
                    elif pol=='yx':
                        datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.resyx[ii]+2*ss+
                                      fmt % rp.resyxerr[ii]+'\n')
                else:
                    if pol=='xy':
                        datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.resxy[ii]+2*ss+
                                      fmt % (rp.resxy[ii]*reserr/100.)+'\n')
                    elif pol=='yx':
                        datafid.write(2*ss+'RhoZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.resyx[ii]+2*ss+
                                      fmt % (rp.resyx[ii]*reserr/100.)+'\n')
                
                #write phase components
                if phaseerr=='data':
                    if pol=='xy':
                        datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.phasexy[ii]+2*ss+
                                      fmt % rp.phasexyerr[ii]+'\n')
                    if pol=='yx':
                        datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.phaseyx[ii]+2*ss+
                                      fmt % rp.phaseyxerr[ii]+'\n')
                else:
                    if pol=='xy':
                        datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.phasexy[ii]+2*ss+
                                      fmt % (phaseerr/100.*(180/np.pi))+'\n')
                    if pol=='yx':
                        datafid.write(2*ss+'PhsZ'+pol+2*ss+str(ii+1)+2*ss+'0'+
                                      2*ss+'1'+2*ss+fmt % rp.phaseyx[ii]+2*ss+
                                      fmt % (phaseerr/100.*(180/np.pi))+'\n')
            datafid.close()
            print 'Wrote Data File: ',dfilesave

    def make1DModelFile(self,savepath=None,nlayers=100,bottomlayer=10000,
                        basestep=10,z1layer=50,airlayerheight=10000):
        """
        Makes a 1D model file for Occam1D.  
        
        Arguments:
        ----------
        
            **savepath** :path to save file to, if just path saved as 
                          savepath\model.mod, if None defaults to dirpath
                          
            **nlayers** : number of layers
            
            **bottomlayer** : depth of bottom layer in meters
            
            **basestep** : numerical base of logarithmic depth step 10 or 2 or 
                          1 for linear
                          
            **z1layer** : depth of first layer in meters
            
            **airlayerheight** : height of air layers in meters
        
        Returns:
        --------
        
            **modelfilename** = full path to model file
            
        ..Note: This needs to be redone.
        """
        
        
        ss='   '
        if savepath==None:
            if self.dirpath:
                savepath=self.dirpath
            else:
                raise IOError('No savepath found.  Please input one.')
                
        elif savepath.find('.')==-1:
            if not os.path.exists(savepath):
                os.mkdir(savepath)
            modfn=os.path.join(savepath,'Model1D')
        else:
            modfn=savepath
        
        #---------need to refine this-------------------- 
        
        layers=np.logspace(np.log10(z1layer),np.log10(bottomlayer),num=nlayers)      
        
        #make the model file
        modfid=open(modfn,'w')
        modfid.write('Format: Resistivity1DMod_1.0'+'\n')
        modfid.write('#LAYERS:    '+str(nlayers+3)+'\n')
        modfid.write('!Set free values to -1 or ? \n')
        modfid.write('!penalize between 1 and 0,'+
                     '0 allowing jump between layers and 1 smooth. \n' )
        modfid.write('!preference is the assumed resistivity on linear scale. \n')
        modfid.write('!pref_penalty needs to be put if preference is not 0 [0,1]. \n')
        modfid.write('! top_depth'+ss+'resistivity'+ss+'penalty'+ss+'preference'+ss+
                     'pref_penalty \n')
        modfid.write(ss+'-10000'+ss+'1d12'+ss+'0'+ss+'0'+ss+'0'+ss+'!air layer \n')
        modfid.write(ss+'0'+ss+'-1'+ss+'0'+ss+'0'+ss+'0'+ss+'!first ground layer \n')
        for ll in layers:
            modfid.write(ss+str(ll)+ss+'-1'+ss+'1'+ss+'0'+ss+'0'+'\n')
        
        modfid.close()
        print 'Wrote Model file: ',modfn
        
        self.modelfn=modfn

    def make1DInputFile(self,savepath=None,imode='TE',roughtype=1,
                        maxiter=100,targetrms=1.0,rhostart=100,
                        description='1dInv',lagrange=5.0,roughness=1.0E7,
                        debuglevel=1,iteration=0,misfit=100.0):
        """
        Make a 1D input file for Occam 1D
        
        Arguments:
        ---------
            **savepath** : full path to save input file to, if just path then 
                           saved as savepath/input
            modelfile = full path to model file, if None then assumed to be in 
                        savepath/model.mod
            datafile = full path to data file, if None then assumed to be in 
                        savepath/data.data
            roughtype = roughness type
            maxiter = maximum number of iterations
            targetrms = target rms value
            rhostart = starting resistivity value on linear scale
            paramcount = 
        """
        
        
        ss='   '
        
        #make input data file name
        if os.path.basename(savepath).find('.')==-1:
            if not os.path.exists(savepath):
                os.mkdir(savepath)
            self.inputfn=os.path.join(savepath,'Input1D')
        else:
            self.inputfn=savepath
            
        if not self.modelfn:
            if self.dirpath:
                modelfile=os.path.join(self.dirpath,'Model1D')
            else:
                raise IOError('No savepath.  Please input one.')
                
        #try to get data file name 
        if imode=='TE':
            if not self.datafn_te:
                if self.dirpath:
                    dfn=os.path.join(self.dirpath,'TEData.dat')
                    if os.path.isfile(dfn)==True:
                        self.datafn_te=dfn
                    else:
                        raise IOError('No TE data file found. Please input one.')
                else:
                    raise IOError('No savepth found. Please input one.')
            else:
                pass
        if imode=='TM':
            if not self.datafn_tm:
                if self.dirpath:
                    dfn=os.path.join(self.dirpath,'TMData.dat')
                    if os.path.isfile(dfn)==True:
                        self.datafn_tm=dfn
                    else:
                        raise IOError('No TM data file found. Please input one.')
                else:
                    raise IOError('No savepth found. Please input one.')
            else:
                pass

        #read in the model and get number of parameters
        mdict=self.read1DModelFile()
        paramcount=mdict['nparam']        
        
        #write input file
        infid=open(self.inputfn,'w')
        infid.write('Format:             OCCAMITER_FLEX      ! Flexible format \n')
        infid.write('Description:        '+description+'     !For your own notes. \n')
        infid.write('Model File:         '+modelfile+'       \n')
        if imode=='TE':
            infid.write('Data File:          '+self.datafn_te+'        \n')                                                                     
        if imode=='TM':
            infid.write('Data File:          '+self.datafn_tm+'        \n')                                                                     
        infid.write('Date/Time:          '+time.ctime()+'\n')         
        infid.write('Max Iter:           '+str(maxiter)+'\n')
        infid.write('Target Misfit:      '+str(targetrms)+'\n')
        infid.write('Roughness Type:     '+str(roughtype)+'\n')
        infid.write('!Model Bounds:      min,max             ! Optional, places bounds'+
                    ' on log10(rho) values. \n')
        infid.write('!Model Value Steps: stepsize            ! Optional, forces model'+
                    ' into discrete steps of stepsize. \n')
        infid.write('Debug Level:        '+str(debuglevel)+
                    ' '*19+'! Console output. '+
                    '0: minimal, 1: default, 2: detailed \n')
        infid.write('Iteration:          '+str(iteration)+
                    ' '*19+'! Iteration number,'+
                    ' use 0 for starting from scratch. \n')
        infid.write('Lagrange Value:     '+str(lagrange)+
                    ' '*17+'! log10(largrance '+
                    'multiplier), starting value.\n')
        infid.write('Roughness Value:    '+str(roughness)+
                    ' '*10+'! Roughness of last'+
                    ' model, ignored on startup. \n')
        infid.write('Misfit Value:       '+str(misfit)+
                    ' '*15+'! Misfit of model listed'+
                    'below. Ignored on startup.\n')
        infid.write('Misfit Reached:     0	                ! 0: not reached,'+
                    ' 1: reached.  Useful when restarting.\n')
        infid.write('Param Count:        '+str(paramcount)+
                    ' '*17+'! Number of free' +
                    ' inversion parameters. \n')
        for ii in range(paramcount):
            infid.write(ss+str(np.log10(rhostart))+'\n')
        
        infid.close()
        print 'Wrote Input File: ',self.inputfn
    
    def read1DModelFile(self):
        """
        
        will read in model 1D file
        
        Arguments:
        ----------
            **modelfn** : full path to model file
            
        Returns:
        --------
            **mdict** : dictionary of values with keys: 
                
                *depth* : depth of model in meters
                
                *res* : value of resisitivity
                
                *pen* : penalty
                
                *pre* : preference
                
                *prefpen* : preference penalty
                
                
        """
        if not self.modelfn:
            raise IOError('No input file found.  Please input one.')
            
        mfid=open(self.modelfn,'r')
        mlines=mfid.readlines()
        mfid.close()
        
        mdict={}
        mdict['nparam']=0
        for key in ['depth','res','pen','pref','prefpen']:
            mdict[key]=[]
        
        for mm,mline in enumerate(mlines):
            if mline.find('!')==0:
                pass
            elif mline.find(':')>=0:
                mlst=mline.strip().split(':')
                mdict[mlst[0]]=mlst[1]
            else:
                mlst=mlst=mline.strip().split()
                mdict['depth'].append(float(mlst[0]))
                if mlst[1]=='?':
                    mdict['res'].append(-1)
                elif mlst[1]=='1d12':
                    mdict['res'].append(1.0E12)
                else:
                    try:
                        mdict['res'].append(float(mlst[1]))
                    except ValueError:
                        mdict['res'].append(-1)
                mdict['pen'].append(float(mlst[2]))
                mdict['pref'].append(float(mlst[3]))
                mdict['prefpen'].append(float(mlst[4]))
                if mlst[1]=='-1' or mlst[1]=='?':
                    mdict['nparam']+=1
                    
        #make everything an array
        for key in ['depth','res','pen','pref','prefpen']:
                mdict[key]=np.array(mdict[key])
        
        #make dictionary an attribute of Occam1D class            
        self.mdict=mdict
    
    def read1DInputFile(self):
        """
        reads in a 1D input file
        
        Arguments:
        ---------
            **inputfn** : full path to input file
        
        Returns:
        --------
            **indict** : dictionary with keys following the header and
            
                *res* : an array of resistivity values
        """
        if not self.inputfn:
            raise IOError('No input file found.  Please input one.')
            
        infid=open(self.inputfn,'r')
        ilines=infid.readlines()
        infid.close()
    
        self.indict={}
        res=[]
        
        #split the keys and values from the header information
        for iline in ilines:
            if iline.find(':')>=0:
                ikey=iline[0:20].strip()
                ivalue=iline[20:].split('!')[0].strip()
                self.indict[ikey]=ivalue
            else:
                try:
                    res.append(float(iline.strip()))
                except ValueError:
                    pass
                
        #make the resistivity array ready for models to be input
        self.indict['res']=np.zeros((len(res),3))
        self.indict['res'][:,0]=res


    def read1DdataFile(self,imode='TE'):
        """
        reads a 1D data file
        
        Arguments:
        ----------
            **datafile** : full path to data file
            
            **imode** : mode to read from can be TE or TM
        
        Returns:
        --------
            **rpdict** : dictionary with keys:
                
                *freq* : an array of frequencies with length nf
                
                *resxy* : TE resistivity array with shape (nf,4) for (0) data,
                          (1) dataerr, (2) model, (3) modelerr
                         
                *resyx* : TM resistivity array with shape (nf,4) for (0) data,
                          (1) dataerr, (2) model, (3) modelerr
                         
                *phasexy* : TE phase array with shape (nf,4) for (0) data,
                            (1) dataerr, (2) model, (3) modelerr
                
                *phaseyx* : TM phase array with shape (nf,4) for (0) data,
                            (1) dataerr, (2) model, (3) modelerr
        """            
        
        #get the data file for the correct mode
        if imode=='TE':
            if not self.datafn_te:
                raise IOError('No TE data file found.  Please input one.')
                
            dfid=open(self.datafn_te,'r')
            
        elif imode=='TM':
            if not self.datafn_tm:
                raise IOError('No TM data file found.  Please input one.')
                
            dfid=open(self.datafn_te,'r')
        
        #read in lines
        dlines=dfid.readlines()
        dfid.close()
        
        #make a dictionary of all the fields found so can put them into arrays
        finddict={}
        for ii,dline in enumerate(dlines):
            if dline.find('#')<=3:
                fkey=dline[2:].strip().split(':')[0]
                fvalue=ii
                finddict[fkey]=fvalue
                
        #get number of frequencies
        nfreq=int(dlines[finddict['Frequencies']][2:].strip().split(':')[1].strip())
        
        #frequency list
        freq=np.array([float(ff) for ff in dlines[finddict['Frequencies']+1:
                                                            finddict['Receivers']]])
                
        #data dictionary to put things into
        #check to see if there is alread one, if not make a new one
        try:
            self.rpdict
        except NameError:
            self.rpdict={'freq':freq,
                         'resxy':np.zeros((4,nfreq)),
                         'resyx':np.zeros((4,nfreq)),
                         'phasexy':np.zeros((4,nfreq)),
                         'phaseyx':np.zeros((4,nfreq))
                         }
        
        #get data        
        for dline in dlines[finddict['Data']+1:]:
            if dline.find('!')==0:
                pass
            else:
                dlst=dline.strip().split()
                if len(dlst)>4:
                    jj=int(dlst[1])-1
                    dvalue=float(dlst[4])
                    derr=float(dlst[5])
                    if dlst[0]=='RhoZxy' or dlst[0]=='103':
                        self.rpdict['resxy'][0,jj]=dvalue
                        self.rpdict['resxy'][1,jj]=derr
                    if dlst[0]=='PhsZxy' or dlst[0]=='104':
                        self.rpdict['phasexy'][0,jj]=dvalue
                        self.rpdict['phasexy'][1,jj]=derr
                    if dlst[0]=='RhoZyx' or dlst[0]=='105':
                        self.rpdict['resyx'][0,jj]=dvalue
                        self.rpdict['resyx'][1,jj]=derr
                    if dlst[0]=='PhsZyx' or dlst[0]=='106':
                        self.rpdict['phaseyx'][0,jj]=dvalue
                        self.rpdict['phaseyx'][1,jj]=derr
        

    def read1DIterFile(self,iterfn,imode='TE'):
        """
        read an 1D iteration file
        
        Arguments:
        ----------
            **imode** : mode to read from 
        
        Returns:
        --------
            **itdict** : dictionary with keys of the header:
                
            **mdict['res']** : fills this array with the appropriate values
                               (0) for data, (1) TE, (2) TM
                
        """
        
        self.read1DModelFile()
        
        freeparams=np.where(self.mdict['res']==-1)[0]
        
        if imode=='TE':
            self.iter_te=iterfn
            ifid=open(self.iterfn_te,'r')
        elif imode=='TM':
            self.iter_tm=iterfn
            ifid=open(self.iterfn_tm,'r')
            
        ilines=ifid.readlines()
        ifid.close()
        
        self.itdict={}
        model=[]    
        for ii,iline in enumerate(ilines):
            if iline.find(':')>=0:
                ikey=iline[0:20].strip()
                ivalue=iline[20:].split('!')[0].strip()
                self.itdict[ikey]=ivalue
            else:
                try:
                    ilst=iline.strip().split()
                    for kk in ilst:
                        model.append(float(kk))
                except ValueError:
                    pass
        
        #put the model values into the model dictionary into the res array
        #for easy manipulation and access.  Also so you can compare TE and TM        
        model=np.array(model)
        if imode=='TE':
            self.mdict['res'][:,1]=self.mdict['res'][:,0]
            self.mdict['res'][freeparams,1]=model
        if imode=='TM':
            self.mdict['res'][:,2]=self.mdict['res'][:,0]
            self.mdict['res'][freeparams,2]=model


    def read1DRespFile(self,respfn):
        """
        read response file
        
        Arguments:
        ---------
            **repsfn** : full path to response file
            
        Returns:
        --------
            **rpdict** : dictionary with keys:
                
                *freq* : an array of frequencies with length nf
                
                *resxy* : TE resistivity array with shape (nf,4) for (0) data,
                          (1) dataerr, (2) model, (3) modelerr
                         
                *resyx* : TM resistivity array with shape (nf,4) for (0) data,
                          (1) dataerr, (2) model, (3) modelerr
                         
                *phasexy* : TE phase array with shape (nf,4) for (0) data,
                            (1) dataerr, (2) model, (3) modelerr
                
                *phaseyx* : TM phase array with shape (nf,4) for (0) data,
                            (1) dataerr, (2) model, (3) modelerr
        """
               
        
        dfid=open(respfn,'r')
        
        dlines=dfid.readlines()
        dfid.close()
    
        finddict={}
        for ii,dline in enumerate(dlines):
            if dline.find('#')<=3:
                fkey=dline[2:].strip().split(':')[0]
                fvalue=ii
                finddict[fkey]=fvalue
        nfreq=int(dlines[finddict['Frequencies']][2:].strip().split(':')[1].strip())
        
        #frequency list
        freq=np.array([float(ff) for ff in dlines[finddict['Frequencies']+1:
                                                            finddict['Receivers']]])
                
        #data dictionary
        try:
            self.rpdict
        except NameError:
            self.rpdict={'freq':freq,
                        'resxy':np.zeros((4,nfreq)),
                        'resyx':np.zeros((4,nfreq)),
                        'phasexy':np.zeros((4,nfreq)),
                        'phaseyx':np.zeros((4,nfreq))
                        }
                
        for dline in dlines[finddict['Data']+1:]:
            if dline.find('!')==0:
                pass
            else:
                dlst=dline.strip().split()
                if len(dlst)>4:
                    jj=int(dlst[1])-1
                    dvalue=float(dlst[4])
                    derr=float(dlst[5])
                    rvalue=float(dlst[6])
                    rerr=float(dlst[7])
                    if dlst[0]=='RhoZxy' or dlst[0]=='103':
                        self.rpdict['resxy'][0,jj]=dvalue
                        self.rpdict['resxy'][1,jj]=derr
                        self.rpdict['resxy'][2,jj]=rvalue
                        self.rpdict['resxy'][3,jj]=rerr
                    if dlst[0]=='PhsZxy' or dlst[0]=='104':
                        self.rpdict['phasexy'][0,jj]=dvalue
                        self.rpdict['phasexy'][1,jj]=derr
                        self.rpdict['phasexy'][2,jj]=rvalue
                        self.rpdict['phasexy'][3,jj]=rerr
                    if dlst[0]=='RhoZyx' or dlst[0]=='105':
                        self.rpdict['resyx'][0,jj]=dvalue
                        self.rpdict['resyx'][1,jj]=derr
                        self.rpdict['resyx'][2,jj]=rvalue
                        self.rpdict['resyx'][3,jj]=rerr
                    if dlst[0]=='PhsZyx' or dlst[0]=='106':
                        self.rpdict['phaseyx'][0,jj]=dvalue
                        self.rpdict['phaseyx'][1,jj]=derr
                        self.rpdict['phaseyx'][2,jj]=rvalue
                        self.rpdict['phaseyx'][3,jj]=rerr
    
    def plot1D(self,respfn,iterfn,imode='TE',fignum=1,ms=4,dpi=150):
        """
        
        """

        #color for data
        cted=(0,0,1)
        ctmd=(1,0,0)
        
        #color for occam model
        ctem=(0,.1,.8)
        ctmm=(.8,.1,0)
        
        try:
            self.modelfn
        except NameError:
            if not self.dirpath:
                self.dirpath=os.path.dirname(respfn)
                
            self.modelfn=os.path.join(self.dirpath,'Model1D')
            if os.path.isfile(self.modelfn)==False:
                raise IOError('Could not find '+self.modelfn)
        
        self.respfn=respfn

        #read in data
        self.read1DRespFile(self.respfn)
        if imode=='TE':
            self.iter_te=iterfn
            self.read1DIterFile(self.iter_te,imode='TE')
            
        elif imode=='TM':
            self.iter_tm=iterfn
            self.read1DIterFile(self.iter_tm,imode='TM')
            
        elif imode=='both':
            if type(iterfn) is not list or type(iterfn) is not tuple:
                raise IOError('Please enter iteration files as a list or tuple.')
            else:
                self.iter_te=iterfn[0]
                self.read1DIterFile(self.iter_te,imode='TE')
                
                self.iter_tm=iterfn[1]
                self.read1DIterFile(self.iter_tm,imode='TM')
                
        period=1/self.rpdict['freq']
        
        #make a grid of subplots
        gs=gridspec.GridSpec(6,5,hspace=.25,wspace=.75)
        
        #make a figure
        fig=plt.figure(fignum,[8,8],dpi=dpi)
        
        #subplot resistivity
        axr=fig.add_subplot(gs[:4,:4])
        
        #subplot for phase
        axp=fig.add_subplot(gs[4:,:4],sharex=axr)
        
        #check for data in resistivity
        rxy=np.where(self.rpdict['resxy'][0]!=0)[0]
        ryx=np.where(self.rpdict['resyx'][0]!=0)[0]
        
        pxy=np.where(self.rpdict['phasexy'][0]!=0)[0]
        pyx=np.where(self.rpdict['phaseyx'][0]!=0)[0]
        
        #check to make sure a model was read in for resistivity
        rxym=np.where(self.rpdict['resxy'][2]!=0)[0]
        ryxm=np.where(self.rpdict['resyx'][2]!=0)[0]
        
        pxym=np.where(self.rpdict['phasexy'][2]!=0)[0]
        pyxm=np.where(self.rpdict['phaseyx'][2]!=0)[0]
        
        if imode=='TE':
            titlestr='$Z_{TE}$'
            #plot data resistivity 
            if len(rxy)!=0:
                r1=axr.loglog(period[rxy],self.rpdict['resxy'][0][rxy],
                              ls='None',marker='o',color='k',mfc='k',ms=ms)

            #plot data phase
            if len(pxy)!=0:
                p1=axp.semilogx(period[pxy],self.rpdict['phasexy'][0][pxy],
                          ls='None',marker='o',color='k',mfc='k',ms=ms)
                          
            #plot model resistivity
            if len(rxym)!=0:
                r2=axr.loglog(period[rxym],self.rpdict['resxy'][2][rxym],
                              ls=':',color='b',lw=2)
            #plot model phase                 
            if len(pxym)!=0:
                p2=axp.semilogx(period[pxym],self.rpdict['phasexy'][2][pxym],
                          ls=':',color='b')
            
            #add legend
            axr.legend([r1,r2],['Data','Model'],loc='upper left',markerscale=2,
                       borderaxespad=.05,
                       labelspacing=.08,
                       handletextpad=.15,borderpad=.05)
            
        elif imode=='TM':
            titlestr='$Z_{TM}$'
            #plot data resistivity 
            if len(ryx)!=0:
                r1=axr.loglog(period[ryx],self.rpdict['resyx'][0][ryx],
                              ls='None',marker='o',color='k',mfc='k',ms=ms)
            #plot data phase
            if len(pyx)!=0:
                p1=axp.semilogx(period[pyx],self.rpdict['phaseyx'][0][pyx],
                          ls='None',marker='o',color='k',mfc='k',ms=ms)
                          
            #plot model resistivity
            if len(ryxm)!=0:
                r2=axr.loglog(period[ryxm],self.rpdict['resyx'][2][ryxm],
                              ls=':',color='b',lw=2)
            #plot model phase                 
            if len(pyxm)!=0:
                p2=axp.semilogx(period[pyxm],self.rpdict['phaseyx'][2][pyxm],
                          ls=':',color='b')
            if len(ryx)!=0:
                r1=axr.loglog(period[ryx],self.rpdict['resyx'][0][ryx],
                              ls='None',marker='o',color='k',mfc='k',ms=ms)
                
            axr.legend([r1,r2],['Data','Model'],loc='upper left',markerscale=2,
                       borderaxespad=.05,
                       labelspacing=.08,
                       handletextpad=.15,borderpad=.05)
        
        
        elif imode=='both':
            #plot data resistivity 
            if len(rxy)!=0:
                r1te=axr.loglog(period[rxy],self.rpdict['resxy'][0][rxy],
                              ls='None',marker='s',color='k',mfc='k',ms=ms)
            if len(ryx)!=0:
                r1tm=axr.loglog(period[ryx],self.rpdict['resyx'][0][ryx],
                              ls='None',marker='o',color='k',mfc='k',ms=ms)

            #plot data phase
            if len(pxy)!=0:
                p1te=axp.semilogx(period[pxy],self.rpdict['phasexy'][0][pxy],
                          ls='None',marker='s',color='k',mfc='k',ms=ms)
            
            if len(pyx)!=0:
                p1tm=axp.semilogx(period[pyx],self.rpdict['phaseyx'][0][pyx],
                          ls='None',marker='o',color='k',mfc='k',ms=ms)
                          
            #plot model resistivity
            if len(rxym)!=0:
                r2te=axr.loglog(period[rxym],self.rpdict['resxy'][2][rxym],
                              ls=':',color='b',lw=2)
        
            if len(ryxm)!=0:
                r2tm=axr.loglog(period[ryxm],self.rpdict['resyx'][2][ryxm],
                              ls=':',color='r',lw=2)
            #plot model phase                 
            if len(pxym)!=0:
                p2=axp.semilogx(period[pxym],self.rpdict['phasexy'][2][pxym],
                          ls=':',color='b')
            if len(pyxm)!=0:
                p2=axp.semilogx(period[pyxm],self.rpdict['phaseyx'][2][pyxm],
                          ls=':',color='r')
            
            #add legend
            axr.legend([r1te,r2te,r1tm,r2tm],
                       ['Data$_{TE}$','Model$_{TE}$',
                        'Data$_{TM}$','Model$_{TM}$'],
                        loc='upper left',markerscale=2,
                       borderaxespad=.05,
                       labelspacing=.08,
                       handletextpad=.15,borderpad=.05)

                          
        axr.grid(True,alpha=.4)
        axr.set_xticklabels(['' for ii in range(10)])
        axp.grid(True,alpha=.4)
        axp.yaxis.set_major_locator(MultipleLocator(10))
        axp.yaxis.set_minor_locator(MultipleLocator(1))
        
        axr.set_ylabel('App. Res. ($\Omega \cdot m$)',
                       fontdict={'size':12,'weight':'bold'})
        axp.set_ylabel('Phase (deg)',
                       fontdict={'size':12,'weight':'bold'})
        axp.set_xlabel('Period (s)',fontdict={'size':12,'weight':'bold'})
        axr.yaxis.set_label_coords(-.15,.5)
        axp.yaxis.set_label_coords(-.15,.5)
        plt.suptitle(titlestr,fontsize=14,fontweight='bold')
        
        #plot 1D inversion
        axm=fig.add_subplot(gs[:,4])
        depthp=np.array([self.mdict['depth'][0:ii+1].sum() 
                        for ii in range(len(self.mdict['depth']))])[1:]
        if imode=='TE':
            modelresp=abs(10**self.mdict['res'][1:,1])
            axm.loglog(modelresp[::-1],depthp[::-1],ls='steps-',color='b')
        elif imode=='TM':
            modelresp=abs(10**self.mdict['res'][1:,2])
            axm.loglog(modelresp[::-1],depthp[::-1],ls='steps-',color='b')
        elif imode=='both':
            modelrespte=abs(10**self.mdict['res'][1:,1])
            axm.loglog(modelrespte[::-1],depthp[::-1],ls='steps-',color='b')
            modelresptm=abs(10**self.mdict['res'][1:,1])
            axm.loglog(modelresptm[::-1],depthp[::-1],ls='steps-',color='r')
        
        print (depthp[-1],depthp[0])
        axm.set_ylim(ymin=depthp[-1],ymax=depthp[0])
    #    axm.set_xlim(xmax=10**3)
        axm.set_ylabel('Depth (m)',fontdict={'size':12,'weight':'bold'})
        axm.set_xlabel('Resistivity ($\Omega \cdot m$)',
                       fontdict={'size':12,'weight':'bold'})
        axm.grid(True,which='both')
        
        plt.show()
    

def make2DdataFile(edipath,mmode='both',savepath=None,stationlst=None,title=None,
                   thetar=0,resxyerr=10,resyxerr=10,phasexyerr=10,phaseyxerr=10,
                   ss=3*' ',fmt='%2.6f',freqstep=1,plotyn='y',lineori='ew',
                   tippererr=None,ftol=.05):
    """
    make2DdataFile will make a data file for occam2D.  
    
    Input:
        edipath = path to edifiles
        mmode = modes to invert for.  Can be: 
                'both' -> will model both TE and TM modes
                'TM'   -> will model just TM mode
                'TE'   -> will model just TE mode
        savepath = path to save the data file to, this can include the name of
                   the data file, if not the file will be named:
                       savepath\Data.dat or edipath\Data.dat if savepath=None
        stationlst = list of stations to put in the data file, doesn't need to
                     be in order, the relative distance will be calculated
                     internally.  If stationlst=None, it will be assumed all the
                     files in edipath will be input into the data file
        title = title input into the data file
        thetar = rotation angle (deg) of the edifiles if you want to align the
                 components with the profile.  Angle is on the unit circle with 
                 an orientation that north is 0 degree, east -90.
        resxyerr = percent error in the res_xy component (TE), 
                  can be entered as 'data' where the errors from the data are
                  used.  
        resyxerr = percent error in the res_yx component (TM), 
                  can be entered as 'data' where the errors from the data are
                  used.  
        phasexyerr = percent error in the phase_xy component (TE), 
                  can be entered as 'data' where the errors from the data are
                  used.  
        phaseyxerr = percent error in the phase_yx component (TM), 
                  can be entered as 'data' where the errors from the data are
                  used.  
        ss = is the spacing parameter for the data file
        fmt = format of the numbers for the data file, see string formats for 
              a full description
        freqstep = take frequencies at this step, so if you want to take every
                   third frequency enter 3.  
                   Can input as a list of specific frequencies.  Note that the
                   frequencies must match the frequencies in the EDI files,
                   otherwise they will not be input.  
        plotyn = y or n to plot the stations on the profile line.
        lineori = predominant line orientation with respect to geographic north
                 ew for east-west line-> will orientate so first station is 
                                         farthest to the west
                 ns for north-south line-> will orientate so first station is 
                                         farthest to the south
        tippererr = error for tipper in percent.  If this value is entered than
                    the tipper will be included in the inversion, if the value
                    is None than the tipper will not be included.
              
    Output:
        datfilename = full path of data file
                 
    """
    import matplotlib.pyplot as plt
    import mtpy.core.mttools as mt
    import mtpy.utils.latlongutmconversion as utm2ll
    
    
    if abs(thetar)>2*np.pi:
        thetar=thetar*(np.pi/180)
    #create rotation matrix
    rotmatrix=np.array([[np.cos(thetar), np.sin(thetar)],
                         [-np.sin(thetar), np.cos(thetar)]])
    
    #-----------------------Station Locations-----------------------------------    
    #create a list to put all the station dictionaries into
    surveylst=[]
    eastlst=[]
    northlst=[]
    pstationlst=[]
    freqlst=[]
    
    if stationlst==None:
        stationlst=[edifile[:-4] 
            for edifile in os.listdir(edipath) if edifile.find('.edi')]
    
    for kk,station in enumerate(stationlst):
        #search for filenames in the given directory and match to station name
        for filename in os.listdir(edipath):
            if fnmatch.fnmatch(filename,station+'*.edi'):
                print 'Found station edifile: ', filename
                surveydict={} #create a dictionary for the station data and info
                edifile=os.path.join(edipath,filename) #create filename path
                z1=Z.Z(edifile)
#                edidict=mt.readedi(edifile) #read in edifile as a dictionary
                freq=z1.frequency                
#                freq=edidict['frequency']
                #check to see if the frequency is in descending order
                if freq[0]<freq[-1]:
                    freq=freq[::-1]
                    z=z1.z[::-1,:,:]
                    zvar=z1.zvar[::-1,:,:]
                    tip=z1.tipper[::-1,:,:]
                    tipvar=z1.tippervar[::-1,:,:]
                    
#                    z=edidict['z'][::-1,:,:]
#                    zvar=edidict['zvar'][::-1,:,:]
#                    tip=edidict['tipper'][::-1,:,:]
#                    tipvar=edidict['tippervar'][::-1,:,:]
                    print 'Flipped to descending frequency for station '+station
                else:
                    z=z1.z
                    zvar=z1.zvar
                    tip=z1.tipper
                    tipvar=z1.tippervar
#                    z=edidict['z']
#                    zvar=edidict['zvar']
#                    tip=edidict['tipper']
#                    tipvar=edidict['tippervar']
                #rotate matrices if angle is greater than 0
                if thetar!=0:
                    for rr in range(len(z)):
                        z[rr,:,:]=np.dot(rotmatrix,np.dot(z[rr],rotmatrix.T))
                        zvar[rr,:,:]=np.dot(rotmatrix,np.dot(zvar[rr],
                                                             rotmatrix.T))
                else:
                    pass
                        
#                zone,east,north=utm2ll.LLtoUTM(23,edidict['lat'],edidict['lon'])
                zone,east,north=utm2ll.LLtoUTM(23,z1.lat,z1.lon)
                #put things into a dictionary to sort out order of stations
                surveydict['station']=station
                surveydict['east']=east
                surveydict['north']=north
                surveydict['zone']=zone
                surveydict['z']=z
                surveydict['zvar']=zvar
                surveydict['freq']=freq
                surveydict['tipper']=tip
                surveydict['tippervar']=tipvar
#                surveydict['lat']=edidict['lat']
                surveydict['lat']=z1.lat
#                surveydict['lon']=edidict['lon']
                surveydict['lon']=z1.lon
                freqlst.append(freq)
                eastlst.append(east)
                northlst.append(north)
                pstationlst.append(station)
                surveylst.append(surveydict)
                
    #project stations onto a best fitting line
    #plot a bestfitting line
    p=sp.polyfit(eastlst,northlst,1)
    theta=np.arctan(p[0])
    print 'Profile Line Angle is: {0:.4g} (E=0,N=90)'.format(theta*180/np.pi)
    
    #plot stations on profile line
    if plotyn=='y':
        plt.figure(4)
        plt.title('Projected Stations')
        plt.plot(eastlst,sp.polyval(p,eastlst),'-b',lw=2)
        
    for ii in range(len(surveylst)):
        if surveylst[ii]['zone']!=surveylst[0]['zone']:
            print surveylst[ii]['station']
        d=(northlst[ii]-sp.polyval(p,eastlst[ii]))*np.cos(theta)
        x0=eastlst[ii]+d*np.sin(theta)
        y0=northlst[ii]-d*np.cos(theta)
        surveylst[ii]['east']=x0
        surveylst[ii]['north']=y0
        if plotyn=='y':
            plt.plot(x0,y0,'v',color='k',ms=8,mew=3)
            plt.text(x0,y0+.0005,pstationlst[ii],horizontalalignment='center',
                 verticalalignment='baseline',fontdict={'size':12,
                                                        'weight':'bold'})
        
        #need to figure out a way to account for zone changes
        
        if lineori=='ew': 
            if surveylst[0]['east']<surveylst[ii]['east']:
                surveylst[ii]['offset']=np.sqrt((surveylst[0]['east']-
                                                surveylst[ii]['east'])**2+
                                                (surveylst[0]['north']-
                                                surveylst[ii]['north'])**2)
            elif surveylst[0]['east']>surveylst[ii]['east']:
                surveylst[ii]['offset']=-1*np.sqrt((surveylst[0]['east']-
                                                surveylst[ii]['east'])**2+
                                                (surveylst[0]['north']-
                                                surveylst[ii]['north'])**2)
            else:
                surveylst[ii]['offset']=0
        elif lineori=='ns': 
            if surveylst[0]['north']<surveylst[ii]['north']:
                surveylst[ii]['offset']=np.sqrt((surveylst[0]['east']-
                                                surveylst[ii]['east'])**2+
                                                (surveylst[0]['north']-
                                                surveylst[ii]['north'])**2)
            elif surveylst[0]['north']>surveylst[ii]['north']:
                surveylst[ii]['offset']=-1*np.sqrt((surveylst[0]['east']-
                                                surveylst[ii]['east'])**2+
                                                (surveylst[0]['north']-
                                                surveylst[ii]['north'])**2)
            else:
                surveylst[ii]['offset']=0
    
    #sort by ascending order of distance from first station
    surveylst=sorted(surveylst,key=itemgetter('offset'))
    
    #number of stations read    
    nstat=len(surveylst)    
    
    #--------------------------Match Frequencies--------------------------------
    #a dictionary is created with the frequency as the key and the value is the
    #frequency number in the list. Each edi file is iterated over extracting
    #only the matched frequencies.  This makes it necessary to have the same
    #frequency content in each edifile.    
    
    #make a list to iterate over frequencies
    if type(freqstep) is list or type(freqstep) is not int:
        if type(freqstep[0]) is int:
            #find the median frequency list
            maxflen=max([len(ff) for ff in freqlst])
            farray=np.zeros((nstat,maxflen))
            for ii in range(nstat):
                farray[ii,0:len(freqlst[ii])]=freqlst[ii]
        
            mfreq=np.median(farray,axis=0)
            print len(mfreq),len(freqstep)
            fdict=dict([('%.6g' % mfreq[ff],ii) 
                            for ii,ff in enumerate(freqstep,1) if mfreq[ff]!=0])
        else:
            fdict=dict([('%.6g' % ff,ii) for ii,ff in enumerate(freqstep,1)])
    else:
        #find the median frequency list
        maxflen=max([len(ff) for ff in freqlst])
        farray=np.zeros((nstat,maxflen))
        for ii in range(nstat):
            farray[ii,0:len(freqlst[ii])]=freqlst[ii]
        
        mfreq=np.median(farray,axis=0)
    
        #make a dictionary of values        
        fdict=dict([('%.6g' % ff,ii) for ii,ff in 
                    enumerate(mfreq[range(0,maxflen,freqstep)],1) if ff!=0])

    #print the frequencies to look for to make sure its what the user wants
    #make a list of keys that is sorted in descending order
    klst=[float(dd) for dd in fdict.keys()]
    klst.sort(reverse=True)
    klst=['%.6g' % dd for dd in klst]    
    
    print 'Frequencies to look for are: (# freq(Hz) Period(s)) '
    for key in klst:
        print fdict[key],key, 1./float(key)
    
    #make lists of parameters to write to file    
    reslst=[]
    offsetlst=[]
    stationlstsort=[]
    for kk in range(nstat):
        z=surveylst[kk]['z']
        zvar=surveylst[kk]['zvar']
        freq=surveylst[kk]['freq']
        offsetlst.append(surveylst[kk]['offset'])  
        stationlstsort.append(surveylst[kk]['station'])
        tip=surveylst[kk]['tipper']
        tipvar=surveylst[kk]['tippervar']
        #loop over frequencies to pick out the ones desired
        dflst=range(len(klst))
        for jj,ff in enumerate(freq):
            #jj is the index of edi file frequency list, this index corresponds
            #to the impedance tensor component index
            #ff is the frequency from the edi file frequency list
            try:
                #nn is the frequency number out of extracted frequency list
                nn=fdict['%.6g' % ff]
                            #calculate resistivity 
                wt=.2/(ff)
                resxy=wt*abs(z[jj,0,1])**2
                resyx=wt*abs(z[jj,1,0])**2
        
                #calculate the phase putting the yx in the 1st quadrant        
                phasexy=np.arctan2(z[jj,0,1].imag,z[jj,0,1].real)*(180/np.pi)
                phaseyx=np.arctan2(z[jj,1,0].imag,z[jj,1,0].real)*(180/np.pi)+\
                        180
                #put phases in correct quadrant if should be negative
                if phaseyx>180:
                    phaseyx=phaseyx-360
                    print 'Found Negative Phase',surveylst[kk]['station'],ff    
                
                #calculate errors
                #res_xy (TE)
                if resxyerr=='data':
                    dresxyerr=wt*(abs(z[jj,0,1])+zvar[jj,0,1])**2-resxy
                    lresxyerr=(dresxyerr/resxy)/np.log(10)
                
                else:
                    lresxyerr=(resxyerr/100.)/np.log(10)
                
                #Res_yx(TM)
                if resyxerr=='data':
                    dresyxerr=wt*(abs(z[jj,1,0])+zvar[jj,1,0])**2-resyx
                    lresyxerr=(dresyxerr/resyx)/np.log(10)
                else:
                    lresyxerr=(resyxerr/100.)/np.log(10)
                
                #phase_xy(TE)
                if phasexyerr=='data':
                    dphasexyerr=np.arcsin(zvar[jj,0,1]/abs(z[jj,0,1]))*\
                                (180/np.pi)
                else:
                    dphasexyerr=(phasexyerr/100.)*57/2.
                    
                #phase_yx (TM)
                if phaseyxerr=='data':
                    dphaseyxerr=np.arcsin(zvar[jj,1,0]/abs(z[jj,1,0]))*\
                                (180/np.pi)
                else:
                    dphaseyxerr=(phaseyxerr/100.)*57/2.
                
                #calculate log10 of resistivity as prescribed by OCCAM
                lresyx=np.log10(resyx)
                lresxy=np.log10(resxy)
                
                #if include the tipper
                if tippererr!=None:
                    if tip[jj,0].real==0.0 or tip[jj,1]==0.0:
                        tipyn='n'
                    else:
                        #calculate the projection angle for real and imaginary
                        tipphir=np.arctan(tip[jj,0].real/tip[jj,1].real)-theta
                        tipphii=np.arctan(tip[jj,0].imag/tip[jj,1].imag)-theta
                        
                        #project the tipper onto the profile line
                        projtipr=np.sqrt(tip[jj,0].real**2+tip[jj,1].real**2)*\
                                  np.cos(tipphir)
                        projtipi=np.sqrt(tip[jj,0].imag**2+tip[jj,1].imag**2)*\
                                  np.cos(tipphii)
                                  
                        #error of tipper is a decimal percentage
                        projtiperr=tippererr/100.
                        
                        tipyn='y'
                        
                    
                #make a list of lines to write to the data file
                if mmode=='both':
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                    fmt % lresxy +ss+fmt % lresxyerr+'\n')
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                    fmt % phasexy +ss+fmt % dphasexyerr+'\n')
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                    fmt % lresyx+ss+fmt % lresyxerr+'\n')
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                    fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                    if tippererr!=None and tipyn=='y':
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                    fmt % projtipr +ss+fmt % projtiperr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                    fmt % projtipi +ss+fmt % projtiperr+'\n')
                elif mmode=='TM':
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                    fmt % lresyx +ss+fmt % lresyxerr+'\n')
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                    fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                    if tippererr!=None and tipyn=='y':
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                    fmt % projtipr +ss+fmt % projtiperr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                    fmt % projtipi +ss+fmt % projtiperr+'\n')
                elif mmode=='TE':
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                    fmt % lresxy+ss+fmt % lresxyerr+'\n')
                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                    fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                    if tippererr!=None and tipyn=='y':
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                    fmt % projtipr +ss+fmt % projtiperr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                    fmt % projtipi +ss+fmt % projtiperr+'\n')
                else:
                    raise NameError('mmode' +mmode+' not defined')
            except KeyError:
                #search around the frequency given by ftol
                try:
                    for key in fdict.keys():
                        if ff>float(key)*(1-ftol) and ff<float(key)*(1+ftol):
                            nn=fdict[key]                           
                            wt=.2/(ff)
                            resxy=wt*abs(z[jj,0,1])**2
                            resyx=wt*abs(z[jj,1,0])**2
                    
                            #calculate the phase putting the yx in the 1st quadrant        
                            phasexy=np.arctan2(z[jj,0,1].imag,z[jj,0,1].real)*\
                                    (180/np.pi)
                            phaseyx=np.arctan2(z[jj,1,0].imag,z[jj,1,0].real)*\
                                    (180/np.pi)+180
                            #put phases in correct quadrant if should be negative
                            if phaseyx>180:
                                phaseyx=phaseyx-360
                                print 'Found Negative Phase',surveylst[kk]['station'],ff    
                            
                            #calculate errors
                            #res_xy (TE)
                            if resxyerr=='data':
                                dresxyerr=wt*(abs(z[jj,0,1])+zvar[jj,0,1])**2-resxy
                                lresxyerr=(dresxyerr/resxy)/np.log(10)
                            
                            else:
                                lresxyerr=(resxyerr/100.)/np.log(10)
                            
                            #Res_yx(TM)
                            if resyxerr=='data':
                                dresyxerr=wt*(abs(z[jj,1,0])+zvar[jj,1,0])**2-resyx
                                lresyxerr=(dresyxerr/resyx)/np.log(10)
                            else:
                                lresyxerr=(resyxerr/100.)/np.log(10)
                            
                            #phase_xy(TE)
                            if phasexyerr=='data':
                                dphasexyerr=np.arcsin(zvar[jj,0,1]/abs(z[jj,0,1]))*\
                                            (180/np.pi)
                            else:
                                dphasexyerr=(phasexyerr/100.)*57/2.
                                
                            #phase_yx (TM)
                            if phaseyxerr=='data':
                                dphaseyxerr=np.arcsin(zvar[jj,1,0]/abs(z[jj,1,0]))*\
                                            (180/np.pi)
                            else:
                                dphaseyxerr=(phaseyxerr/100.)*57/2.
                            
                            #calculate log10 of resistivity as prescribed by OCCAM
                            lresyx=np.log10(resyx)
                            lresxy=np.log10(resxy)
                            
                            #if include the tipper
                            if tippererr!=None:
                                if tip[jj,0].real==0.0 or tip[jj,1]==0.0:
                                    tipyn='n'
                                else:
                                    #calculate the projection angle for real and imaginary
                                    tipphir=np.arctan(tip[jj,0].real/tip[jj,1].real)-theta
                                    tipphii=np.arctan(tip[jj,0].imag/tip[jj,1].imag)-theta
                                    
                                    #project the tipper onto the profile line
                                    projtipr=np.sqrt(tip[jj,0].real**2+tip[jj,1].real**2)*\
                                              np.cos(tipphir)
                                    projtipi=np.sqrt(tip[jj,0].imag**2+tip[jj,1].imag**2)*\
                                              np.cos(tipphii)
                                              
                                    #error of tipper is a decimal percentage
                                    projtiperr=tippererr/100.
                                    
                                    tipyn='y'
                                    
                                
                            #make a list of lines to write to the data file
                            if mmode=='both':
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                                fmt % lresxy +ss+fmt % lresxyerr+'\n')
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                                fmt % phasexy +ss+fmt % dphasexyerr+'\n')
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                                fmt % lresyx+ss+fmt % lresyxerr+'\n')
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                                fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                                if tippererr!=None and tipyn=='y':
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                                fmt % projtipr +ss+fmt % projtiperr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                                fmt % projtipi +ss+fmt % projtiperr+'\n')
                            elif mmode=='TM':
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                                fmt % lresyx +ss+fmt % lresyxerr+'\n')
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                                fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                                if tippererr!=None and tipyn=='y':
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                                fmt % projtipr +ss+fmt % projtiperr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                                fmt % projtipi +ss+fmt % projtiperr+'\n')
                            elif mmode=='TE':
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                                fmt % lresxy+ss+fmt % lresxyerr+'\n')
                                reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                                fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                                if tippererr!=None and tipyn=='y':
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                                fmt % projtipr +ss+fmt % projtiperr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                                fmt % projtipi +ss+fmt % projtiperr+'\n')
                            else:
                                raise NameError('mmode' +mmode+' not defined')    
                        
                            break                         
                        else:
                            pass
        #                           print 'Did not find frequency {0} for station {1}'.format(ff,surveylst[kk]['station'])
                            #calculate resistivity 
                               
                except KeyError:
                    pass
    
    #===========================================================================
    #                             write dat file
    #===========================================================================
    if savepath!=None:
        if os.path.basename(savepath).find('.')>0:
            datfilename=savepath
        else:
            if not os.path.exists(savepath):
                os.mkdir(savepath)
            datfilename=os.path.join(savepath,'Data.dat')
    else:
        datfilename=os.path.join(edipath,'Data.dat')
        
    if title==None:
        title='Occam Inversion'
        
    datfid=open(datfilename,'w')
    datfid.write('FORMAT:'+' '*11+'OCCAM2MTDATA_1.0'+'\n')
    datfid.write('TITLE:            %1.4f-- %s\n'%(theta*180/np.pi,title))
    
    #write station sites
    datfid.write('SITES:'+' '*12+str(nstat)+'\n')
    for station in stationlstsort:
        datfid.write(ss+station+'\n')
    
    #write offsets
    datfid.write('OFFSETS (M):'+'\n')
    for offset in offsetlst:
        datfid.write(ss+fmt % offset+'\n')
    
    #write frequencies
    #writefreq=[freq[ff] for ff in range(0,len(freq),freqstep)]
    datfid.write('FREQUENCIES:'+' '*8+str(len(fdict))+'\n')
    for fkey in klst:
        datfid.write(ss+fmt % float(fkey) +'\n')
    
    #write data block
    datfid.write('DATA BLOCKS:'+' '*10+str(len(reslst))+'\n')
    datfid.write('SITE'+ss+'FREQ'+ss+'TYPE'+ss+'DATUM'+ss+'ERROR'+'\n')
    for ll,datline in enumerate(reslst):
        if datline.find('#IND')>=0:
            print 'Found #IND on line ',ll
            ndline=datline.replace('#IND','00')
            print 'Replaced with 00'
            datfid.write(ndline)
        else:
            datfid.write(datline)
    datfid.close()
    
    print 'Wrote Occam2D data file to: ',datfilename
    
    return datfilename
    
def makeModel(datafilename,niter=20,targetrms=1.0,nlayers=100,nlperdec=30,
              z1layer=50,bwidth=200,trigger=.75,cwd='.',rhostart=100,
              makemodelexe=None, modelname="", use_existing_startup = False, existing_startup_file = None):

    """
    makeModel will make an the input files for occam using Steve Constable's
    MakeModel2DMT.f code.
    
    Inputs:
        datafn = full path to data file
        niter = maximum number of iterations
        targetrms = target root mean square error
        nlayers = total number of layers in mesh
        nlperdec = number of layers per decade
        z1layer = thickness of the first layer in meters
        bwidth = maximum block width for regularization grid in meters
        trigger = triger point to amalgamate blocks
        cwd     = working directory, files are saved here
        rhostart = starting resistivity for homogeneous half space in ohm-m
        use_existing_startup: set True, if an old iteration step output is provided as startup
        existing_startup_file: absolute path for old itereation output to be used as startup

        
            
        
    Outputs:
        meshfn = mesh file for finite element grid saved ats MESH
        inmodelfn = input model, starting model with rhostart as starting value
                    saved as INMODEL
        startupfn = start up filepath, saved as startup
    """
    #get the base name of data file    
    
    olddir = os.path.abspath(os.curdir)
    os.chdir(cwd)

    dfnb=os.path.basename(datafilename)


    #deprecated....not necessary, if path is given in excplicit form
    #put data file into the same directory as MakeModel2DMT
    
    #write input file for MakeModel2DMT
    mmfid=file(os.path.join(cwd,'inputMakeModel.txt'),'w')
    mmfid.write(dfnb+'\n')
    mmfid.write(str(niter)+'\n')    
    mmfid.write(str(targetrms)+'\n')    
    mmfid.write(str(nlayers)+'\n')
    mmfid.write(str(nlperdec)+'\n')
    mmfid.write(str(z1layer)+'\n')
    mmfid.write(str(bwidth)+'\n')
    mmfid.write(str(trigger)+'\n')
    mmfid.write('\n')
    mmfid.close()

    #WRite parameters to local dict for passing to functions:
    parameter_dict={}
    parameter_dict['datafile'] = datafilename
    parameter_dict['n_max_iterations'] = niter
    parameter_dict['targetrms'] = targetrms
    parameter_dict['n_layers'] = nlayers
    parameter_dict['n_layersperdecade'] = nlperdec
    parameter_dict['firstlayer_thickness'] = z1layer
    parameter_dict['max_blockwidth'] = bwidth
    parameter_dict['trigger'] = trigger
    parameter_dict['cwd'] = cwd
    parameter_dict['rho_start'] = rhostart
    parameter_dict['modelname'] = modelname

    #shutil.copy(os.path.join(occampath,'inputMakeModel.txt'),
                #os.path.join(os.path.dirname(datafilename),
                             #'inputMakeModel.txt'))
    
    
    #---call MakeModel2DMT---
    #subprocess.os.system("%s < inputMakeModel.txt"%(makemodelexe))

    
    #change back to original working directory    
    #os.chdir(cdir)
    
    
    meshfn=os.path.join(cwd,'MESH')
    inmodelfn=os.path.join(cwd,'INMODEL')
    startupfn=os.path.join(cwd,'startup')
    
    parameter_dict['meshfn']  = meshfn
    parameter_dict['inmodelfn']  = inmodelfn
        

    if use_existing_startup:
        startupfn =  existing_startup_file

    parameter_dict['startupfn']  = startupfn
    
    #write OCCAM input files directly - no external function needed:
    filelist= makestartfiles(parameter_dict)

    #deprecated....not necessary
    #copy ouput files to savepath
    
    #rewrite mesh so it contains the right number of columns and rows
    #rewriteMesh(meshfn)
    
    #write startup file to have the starting desired starting rho value
    ifid=file(startupfn,'r')
    ilines=ifid.readlines()
    ifid.close()
    
    if rhostart!=100:
        #make startup model a homogeneous half space of rhostart
        rhostart=np.log10(rhostart)
        ifid=open(startupfn,'w')
        for line in ilines:
            if line.find('2.000000')>=0:
                line=line.replace('2.000000','%.6f' % rhostart)
            ifid.write(line)
    ifid.close()
    
    print 'Be sure to check the INMODEL file for clumped numbers near the bottom.'
    print 'Also, check the MESH and startup files to make sure they are correct.'

    #go back to old path:
    os.chdir(olddir)
    
    return filelist


def rewriteMesh(meshfn):
    """
    checkMesh will check to see if the number of lines are correct and the 
    length of the line is correct
    """
    
    #check the mesh
    mfid=file(meshfn,'r')
    mlines=mfid.readlines()
    mfid.close()
    
    #get parameters for number of lines and number of unknowns per line    
    pstr=mlines[1].strip().split()
    nhn=int(pstr[1])
    nvn=(int(pstr[2])-1)*4
    
    print 'Number of horizontal nodes: ',nhn
    print 'Number of vertical nodes: ',nvn
    #find the first line
    for ii,mline in enumerate(mlines[2:],2):
        if mline.find('?')==0:
            qspot=ii
            break

    #rewrite the file to have the proper amount of stuff
    mfid=file(meshfn,'w')
    for line in mlines[0:qspot]:
        mfid.write(line)
    
    for kk in range(qspot,qspot+nvn):
        mfid.write('?'*(nhn-1)+'\n')
    mfid.close()
 

def read2Dmesh(meshfn):
    """
    read a 2D meshfn
    
    Input:
        meshfn = full path to mesh file

    Output:
        hnodes = array of horizontal nodes (column locations (m))
        vnodes = array of vertical nodes (row locations(m))
        mdata = free parameters
        
    Things to do:
        incorporate fixed values
    """
    
    mfid=file(meshfn,'r')
    
    mlines=mfid.readlines()
    
    nh=int(mlines[1].strip().split()[1])-1
    nv=int(mlines[1].strip().split()[2])-1
    
    hnodes=np.zeros(nh)
    vnodes=np.zeros(nv)
    mdata=np.zeros((nh,nv,4),dtype=str)    
    
    #get horizontal nodes
    jj=2
    ii=0
    while ii<nh:
        hline=mlines[jj].strip().split()
        for mm in hline:
            hnodes[ii]=float(mm)
            ii+=1
        jj+=1
    
    #get vertical nodes
    ii=0
    while ii<nv:
        vline=mlines[jj].strip().split()
        for mm in vline:
            vnodes[ii]=float(mm)
            ii+=1
        jj+=1    
    
    #get free parameters        
    for ii,mm in enumerate(mlines[jj+1:]):
        kk=0
        while kk<4:        
            mline=mm.rstrip()
            if mline.find('EXCEPTION')>0:
                break
            for jj in range(nh):
                try:
                    mdata[jj,ii,kk]=mline[jj]
                except IndexError:
                    pass
            kk+=1
    
    return hnodes,vnodes,mdata
    
def read2DInmodel(inmodelfn):
    """
    read an INMODEL file for occam 2D
    
    Input:
        inmodelfn = full path to INMODEL file
    
    Output:
        rows = list of combined data blocks where first number of each list
                represents the number of combined mesh layers for this 
                regularization block.  The second number is the number of 
                columns in the regularization block layer
        cols = list of combined mesh columns for the regularization layer.
               The sum of this list must be equal to the number of mesh
               columns.
        headerdict = dictionary of all the header information including the
                     binding offset
    """
    
    ifid=open(inmodelfn,'r')
    
    headerdict={}
    rows=[]
    cols=[]    
    ncols=[]
    
    ilines=ifid.readlines()
    
    for ii,iline in enumerate(ilines):
        if iline.find(':')>0:
            iline=iline.strip().split(':')
            headerdict[iline[0]]=iline[1]
            #append the last line
            if iline[0].find('EXCEPTIONS')>0:
                cols.append(ncols)
        else:
            iline=iline.strip().split()
            iline=[int(jj) for jj in iline]
            if len(iline)==2:
                if len(ncols)>0:
                    cols.append(ncols)
                rows.append(iline)
                ncols=[]
            elif len(iline)>2:
                ncols=ncols+iline
    
    return rows,cols,headerdict
                
    
def read2DdataFile(datafn):
    """
    read2DdataFile will read in data from a 2D occam data file.  Only supports
    the first 6 data types of occam2D
    
    Input: 
        datafn = full path to data file
    
    Output:
        rplst = list of dictionaries for each station with keywords:
            'station' = station name
            'offset' = relative offset,
            'resxy' = TE resistivity and error as row 0 and 1 ressectively,
            'resyx'= TM resistivity and error as row 0 and 1 respectively,
            'phasexy'= TE phase and error as row 0 and 1 respectively,
            'phaseyx'= Tm phase and error as row 0 and 1 respectively,
            'realtip'= Real Tipper and error as row 0 and 1 respectively,
            'imagtip'= Imaginary Tipper and error as row 0 and 1 respectively
            
            Note: that the resistivity will be in log10 space.  Also, there are
            2 extra rows in the data arrays, this is to put the response from
            the inversion. 
        
        stationlst = list of stations in order from one side of the profile
                     to the other.
        freq = list of frequencies used in the inversion
        title = title, could be useful for plotting.
    """
    
    dfid=open(datafn,'r')
    
    dlines=dfid.readlines()
    #get format of input data
    fmt=dlines[0].strip().split(':')[1].strip()
    
    #get title
    titlestr=dlines[1].strip().split(':')[1].strip()

    if titlestr.find('--')>0:
        tstr=titlestr.split('--')
        theta=tstr[0]
        title=tstr[1]
    else:
        title=titlestr
        theta=0
        print 'Need to figure out angle of profile line'
    #get number of sits
    nsites=int(dlines[2].strip().split(':')[1].strip())
    
    #get station names
    stationlst=[dlines[ii].strip() for ii in range(3,nsites+3)]
    
    #get offsets in meters
    offsets=[float(dlines[ii].strip()) for ii in range(4+nsites,4+2*nsites)]
    
    #get number of frequencies
    nfreq=int(dlines[4+2*nsites].strip().split(':')[1].strip())

    #get frequencies
    freq=[float(dlines[ii].strip()) for ii in range(5+2*nsites,
                                                      5+2*nsites+nfreq)]
                                                      

    #-----------get data-------------------
    #set zero array size the first row will be the data and second the error
    asize=(4,nfreq)
    #make a list of dictionaries for each station.
    rplst=[{'station':station,'offset':offsets[ii],
            'resxy':np.zeros(asize),
            'resyx':np.zeros(asize),
            'phasexy':np.zeros(asize),
            'phaseyx':np.zeros(asize),
            'realtip':np.zeros(asize),
            'imagtip':np.zeros(asize),
            } for ii,station in enumerate(stationlst)]
    for line in dlines[7+2*nsites+nfreq:]:
        ls=line.split()
        #station index
        ss=int(float(ls[0]))-1
        #component key
        comp=str(int(float(ls[2])))
        #frequency index        
        ff=int(float(ls[1]))-1
        #print ls,ss,comp,ff
        #put into array
        #input data
        rplst[ss][occamdict[comp]][0,ff]=float(ls[3]) 
        #error       
        rplst[ss][occamdict[comp]][1,ff]=float(ls[4])
    
    return rplst,stationlst,np.array(freq),title,theta
    
def rewrite2DdataFile(datafn,edipath=None,thetar=0,resxyerr='prev',
                      resyxerr='prev',phasexyerr='prev',phaseyxerr='prev',
                      tippererr=None,mmode='both',flst=None,removestation=None):
    """
    rewrite2DDataFile will rewrite an existing data file so you can redefine 
    some of the parameters, such as rotation angle, or errors for the different
    components or only invert for one mode or add one or add tipper or remove
    tipper.
    
    Inputs:
        datafn = full path to data file to rewrite
        
        rotz = rotation angle with positive clockwise
        
        resxyerr = error for TE mode resistivity (percent) or 'data' for data 
                    or prev to take errors from data file.
        
        resyxerr = error for TM mode resistivity (percent) or 'data' for data
                    or prev to take errors from data file.
                    
        phasexyerr = error for TE mode phase (percent) or 'data' for data
                    or prev to take errors from data file.
                    
        phaseyxerr = error for TM mode phase (percent) or 'data' for data
                    or prev to take errors from data file.
                    
        tippererr = error for tipper (percent) input only if you want to invert
                    for the tipper or 'data' for data errors
                    or prev to take errors from data file.
                    
        mmodes = 'both' for both TE and TM
                 'TE' for TE
                 'TM' for TM
                 
        flst = frequency list in Hz to rewrite, needs to be similar to the 
                datafile, cannot add frequencies
                
        removestation = list of stations to remove if desired
    """
    ss=3*' '
    fmt='%2.6f'
    
    #load the data for the data file    
    rplst,stationlst,freq,title,theta=read2DdataFile(datafn)
    
    #make a dictionary of rplst for easier extraction of data
    rpdict=dict([(station,rplst[ii]) for ii,station in enumerate(stationlst)])

    #remove stations from rplst and stationlst if desired
    if removestation!=None:
        #if removestation is not a list make it one
        if type(removestation) is not list:
            removestation=[removestation]
        
#        #remove station dictionary from rplst
#        for rstation in removestation:
#            for hh,hdict in enumerate(rplst):
#                if hdict['station']==rstation:
#                    rplst.remove(rplst[hh])
        
        #remove station from station list           
        for rstation in removestation:        
            try:
                stationlst.remove(rstation)
            except ValueError:
                print 'Did not find '+rstation
    
    #if flst is not the same as freq make freq=flst
    if flst!=None:
        freq=flst
    
    
    #if the rotation angle is not 0 than need to read the original data in
    if thetar!=0:
        if edipath==None:
            raise IOError('Need to input the edipath to original edifiles to'+
                           ' get rotations correct')
        
        #get list of edifiles already in data file
        edilst=[os.path.join(edipath,edi) for stat in stationlst 
                for edi in os.listdir(edipath) if edi[0:len(stat)]==stat]
        reslst=[]
        for kk,edifn in enumerate(edilst,1):
            imp1=Z.Z(edifn)
            rp=imp1.getResPhase(thetar=thetar)
            imptip=imp1.getTipper()
            tip=imptip.tipper
            station=stationlst[kk-1]
            fdict=dict([('{0:.6g}'.format(fr),ii) for ii,fr in enumerate(imp1.frequency)])
            #loop over frequencies to pick out the ones desired
            for jj,ff in enumerate(freq,1):
                #jj is the index of edi file frequency list, this index corresponds
                #to the impedance tensor component index
                #ff is the frequency from the edi file frequency list
                try:
                    #nn is the frequency number out of extracted frequency list
                    nn=fdict['%.6g' % ff]
                    
                    #calculate resistivity
                    resxy=rp.resxy[nn]
                    resyx=rp.resyx[nn]
            
                    #calculate the phase putting the yx in the 1st quadrant
                    phasexy=rp.phasexy[nn]
                    phaseyx=rp.phaseyx[nn]+180
                    #put phases in correct quadrant if should be negative
                    if phaseyx>180:
                        phaseyx=phaseyx-360
                        print 'Found Negative Phase at',imp1.station,ff    
                    
                    #calculate errors
                    #res_xy (TE)
                    if resxyerr=='data':
                        lresxyerr=(rp.resxyerr[nn]/resxy)/np.log(10)
                    #take errors from data file
                    elif resxyerr=='prev':
                        lresxyerr=rpdict[station]['resxy'][1,jj-1]
                    else:
                        lresxyerr=(resxyerr/100.)/np.log(10)
                    
                    #Res_yx(TM)
                    if resyxerr=='data':
                        lresxyerr=rpdict[station]['resyx'][1,jj-1]
                    #take errors from data file
                    elif resyxerr=='prev':
                        lresyxerr=rpdict[station]['resyx'][1,jj-1]
                    else:
                        lresyxerr=(resyxerr/100.)/np.log(10)
                    
                    #phase_xy(TE)
                    if phasexyerr=='data':
                        dphasexyerr=rp.phasexyerr[nn]
                        #take errors from data file
                    elif phasexyerr=='prev':
                        dphasexyerr=rpdict[station]['phasexy'][1,jj-1]
                    else:
                        dphasexyerr=(phasexyerr/100.)*57/2.
                        
                    #phase_yx (TM)
                    if phaseyxerr=='data':
                        dphaseyxerr=rp.phaseyxerr[nn]
                    elif phaseyxerr=='prev':
                        dphaseyxerr=rpdict[station]['phaseyx'][1,jj-1]
                    else:
                        dphaseyxerr=(phaseyxerr/100.)*57/2.
                    
                    #calculate log10 of resistivity as prescribed by OCCAM
                    lresyx=np.log10(resyx)
                    lresxy=np.log10(resxy)
                    
                    #if include the tipper
                    if tippererr!=None:
                        if tip.tipper[nn,0]==0.0 or tip[nn,1]==0.0:
                            tipyn='n'
                        else:
                            #calculate the projection angle for real and imaginary
                            tipphir=np.arctan(tip[nn,0].real/tip[nn,1].real)-\
                                    theta
                            tipphii=np.arctan(tip[nn,0].imag/tip[nn,1].imag)-\
                                    theta
                            
                            #project the tipper onto the profile line
                            projtipr=np.sqrt(tip[nn,0].real**2+tip[nn,1].real**2)*\
                                      np.cos(tipphir)
                            projtipi=np.sqrt(tip[nn,0].imag**2+tip[nn,1].imag**2)*\
                                      np.cos(tipphii)
                                      
                            #error of tipper is a decimal percentage
                            projtiperr=tippererr/100.
                            
                            tipyn='y'
                        
                    
                    #make a list of lines to write to the data file
                    if mmode=='both':
                        if rpdict[station]['resxy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                        fmt % lresxy +ss+fmt % lresxyerr+'\n')
                        if rpdict[station]['phasexy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                        fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                        if rpdict[station]['resyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                        fmt % lresyx+ss+fmt % lresyxerr+'\n')
                        if rpdict[station]['phaseyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                        fmt % phaseyx+ss+fmt % dphaseyxerr+'\n')
                        if tippererr!=None and tipyn=='y':
                            if rpdict[station]['realtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                            fmt % projtipr+ss+fmt % projtiperr+
                                            '\n')
                            if rpdict[station]['imagtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                            fmt % projtipi+ss+fmt % projtiperr+
                                            '\n')
                    elif mmode=='TM':
                        if rpdict[station]['resyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                        fmt % lresyx +ss+fmt % lresyxerr+'\n')
                        if rpdict[station]['phaseyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                        fmt % phaseyx+ss+fmt % dphaseyxerr+'\n')
                        if tippererr!=None and tipyn=='y':
                            if rpdict[station]['realtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                            fmt % projtipr+ss+fmt % projtiperr+
                                            '\n')
                            if rpdict[station]['imagtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                            fmt % projtipi+ss+fmt % projtiperr+
                                            '\n')
                    elif mmode=='TE':
                        if rpdict[station]['resxy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                        fmt % lresxy +ss+fmt % lresxyerr+'\n')
                        if rpdict[station]['phasexy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                        fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                        if tippererr!=None and tipyn=='y':
                            if rpdict[station]['realtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                            fmt % projtipr+ss+fmt % projtiperr+
                                            '\n')
                            if rpdict[station]['imagtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                            fmt % projtipi+ss+fmt % projtiperr+
                                            '\n')
                    else:
                        raise NameError('mmode' +mmode+' not defined')
                except KeyError:
                    pass
    
    #If no rotation is desired but error bars are than...
    else:
        reslst=[]
        for kk,station in enumerate(stationlst,1):
            srp=rpdict[station]
            nr=srp['resxy'].shape[1]
            #calculate errors and rewrite
            #res_xy (TE)
            if resxyerr!=None:
                lresxyerr=(resxyerr/100.)/np.log(10)
                srp['resxy'][1,:]=np.repeat(lresxyerr,nr)
            
            #Res_yx(TM)
            if resyxerr!=None:
                lresyxerr=(resyxerr/100.)/np.log(10)
                srp['resyx'][1,:]=np.repeat(lresyxerr,nr)
            
            #phase_xy(TE)
            if phasexyerr!=None:
                dphasexyerr=(phasexyerr/100.)*57/2.
                srp['phasexy'][1,:]=np.repeat(dphasexyerr,nr)
                
            #phase_yx (TM)
            if phaseyxerr!=None:
                dphaseyxerr=(phaseyxerr/100.)*57/2.
                srp['phaseyx'][1,:]=np.repeat(dphaseyxerr,nr)
            
            if tippererr!=None:
                #error of tipper is a decimal percentage
                projtiperr=tippererr/100.
                srp['realtip'][1,:]=np.repeat(projtiperr,nr)
                srp['imagtip'][1,:]=np.repeat(projtiperr,nr)
            
            for jj,ff in enumerate(freq,1):
                #make a list of lines to write to the data file
                if mmode=='both':
                    if srp['resxy'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                    fmt % srp['resxy'][0,jj-1]+ss+
                                    fmt % srp['resxy'][1,jj-1]+'\n')
                    if srp['phasexy'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                    fmt % srp['phasexy'][0,jj-1]+ss+
                                    fmt % srp['phasexy'][1,jj-1]+'\n')
                    if srp['resyx'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                    fmt % srp['resyx'][0,jj-1]+ss+
                                    fmt % srp['resyx'][1,jj-1]+'\n')
                    if srp['phaseyx'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                    fmt % srp['phaseyx'][0,jj-1]+ss+
                                    fmt % srp['phaseyx'][1,jj-1]+'\n')
                    if tippererr!=None and tipyn=='y':
                        if srp['realtip'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                    fmt % srp['realtip'][0,jj-1]+ss+
                                    fmt % srp['realtip'][1,jj-1]+'\n')
                        if srp['imagtip'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                    fmt % srp['imagtip'][0,jj-1]+ss+
                                    fmt % srp['imagtip'][1,jj-1]+'\n')
                elif mmode=='TM':
                    if srp['resyx'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                    fmt % srp['resyx'][0,jj-1]+ss+
                                    fmt % srp['resyx'][1,jj-1]+'\n')
                    if srp['phaseyx'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                    fmt % srp['phaseyx'][0,jj-1]+ss+
                                    fmt % srp['phaseyx'][1,jj-1]+'\n')
                    if tippererr!=None and tipyn=='y':
                        if srp['realtip'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                    fmt % srp['realtip'][0,jj-1]+ss+
                                    fmt % srp['realtip'][1,jj-1]+'\n')
                        if srp['imagtip'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                    fmt % srp['imagtip'][0,jj-1]+ss+
                                    fmt % srp['imagtip'][1,jj-1]+'\n')
                elif mmode=='TE':
                    if srp['resxy'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                    fmt % srp['resxy'][0,jj-1]+ss+
                                    fmt % srp['resxy'][1,jj-1]+'\n')
                    if srp['phasexy'][0,jj-1]!=0.0:
                        reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                    fmt % srp['phasexy'][0,jj-1]+ss+
                                    fmt % srp['phasexy'][1,jj-1]+'\n')
                    if tippererr!=None and tipyn=='y':
                        if srp['realtip'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                    fmt % srp['realtip'][0,jj-1]+ss+
                                    fmt % srp['realtip'][1,jj-1]+'\n')
                        if srp['imagtip'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                    fmt % srp['imagtip'][0,jj-1]+ss+
                                    fmt % srp['imagtip'][1,jj-1]+'\n')

    #===========================================================================
    #                             write dat file
    #===========================================================================
    
    #make the file name of the data file
    if datafn.find('RW')>0:
        dfn=datanf
    else:
        dfn=datafn[:-4]+'RW.dat'
        
    nstat=len(stationlst)
        
    if title==None:
        title='Occam Inversion'
        
    datfid=open(dfn,'w')
    datfid.write('FORMAT:'+' '*11+'OCCAM2MTDATA_1.0'+'\n')
    datfid.write('TITLE:'+' '*12+title+'\n')
    
    #write station sites
    datfid.write('SITES:'+' '*12+str(nstat)+'\n')
    for station in stationlst:
        datfid.write(ss+station+'\n')
    
    #write offsets
    datfid.write('OFFSETS (M):'+'\n')
    for station in stationlst:
        datfid.write(ss+fmt % rpdict[station]['offset']+'\n')
    
    #write frequencies
    #writefreq=[freq[ff] for ff in range(0,len(freq),freqstep)]
    datfid.write('FREQUENCIES:'+' '*8+str(len(freq))+'\n')
    for ff in freq:
        datfid.write(ss+fmt % ff +'\n')
    
    #write data block
    datfid.write('DATA BLOCKS:'+' '*10+str(len(reslst))+'\n')
    datfid.write('SITE'+ss+'FREQ'+ss+'TYPE'+ss+'DATUM'+ss+'ERROR'+'\n')
    for ll,datline in enumerate(reslst):
        if datline.find('#IND')>=0:
            print 'Found #IND on line ',ll
            ndline=datline.replace('#IND','00')
            print 'Replaced with 00'
            datfid.write(ndline)
        else:
            datfid.write(datline)
    datfid.close()
    
    print 'Wrote Occam2D data file to: ',dfn
    
    return dfn
                             
def read2DRespFile(respfn,datafn):
    """
    read2DRespFile will read in a response file and combine the data with info 
    from the data file.

    Input:
        respfn = full path to the response file
        datafn = full path to data file

    Outputs:
        for each data array, the rows are ordered as:
            0 -> input data
            1 -> input error
            2 -> model output
            3 -> relative error (data-model)/(input error)
            
        rplst = list of dictionaries for each station with keywords:
            'station' = station name
            'offset' = relative offset,
            'resxy' = TE resistivity 
            'resyx'= TM resistivity 
            'phasexy'= TE phase 
            'phaseyx'= TM phase a
            'realtip'= Real Tipper 
            'imagtip'= Imaginary Tipper 
            
            Note: that the resistivity will be in log10 space.  Also, there are
            2 extra rows in the data arrays, this is to put the response from
            the inversion. 
        
        stationlst = list of stations in order from one side of the profile
                     to the other.
        freq = list of frequencies used in the inversion
        title = title, could be useful for plotting.
        
    """
    
    rplst,stationlst,freq,title,theta=read2DdataFile(datafn)
    
    rfid=open(respfn,'r')
    
    rlines=rfid.readlines()
    for line in rlines:
        ls=line.split()
        #station index
        ss=int(float(ls[0]))-1
        #component key
        comp=str(int(float(ls[2])))
        #frequency index        
        ff=int(float(ls[1]))-1
        #put into array
        #model response
        rplst[ss][occamdict[comp]][2,ff]=float(ls[5]) 
        #relative error        
        rplst[ss][occamdict[comp]][3,ff]=float(ls[6]) 
        
    return rplst,stationlst,np.array(freq),title

def read2DIterFile(iterfn,iterpath=None):
    """
    read2DIterFile will read an iteration file and combine that info from the 
    datafn and return a dictionary of variables.
    
    Inputs:
        iterfn = full path to iteration file if iterpath=None.  If 
                       iterpath is input then iterfn is just the name
                       of the file without the full path.
    
    Outputs:
        idict = dictionary of parameters, keys are verbatim from the file, 
                except for the key 'model' which is the contains the model
                numbers in a 1D array.
        
    """

    #get full paths if not already input
    if iterpath!=None and os.path.dirname(iterfn)=='':
        ifn=os.path.join(iterpath,iterfn)
    else:
        ifn=iterfn
    if os.path.exists(ifn)==False:
        raise IOError('File: '+ifn+' does not exist, check name and path')
        
#    if iterpath!=None and os.path.dirname(datafn)=='':
#        dfn=os.path.join(iterpath,datafn)
#    else:
#        dfn=datafn
#    if os.path.exists(dfn)==False:
#        raise IOError('File: '+dfn+' does not exist, check name and path')
    
    #open file
    ifid=file(ifn,'r')
    ilines=ifid.readlines()
    ifid.close()
    
    #create dictionary to put things
    idict={}
    ii=0
    #put header info into dictionary with similar keys
    while ilines[ii].find('Param')!=0:
        iline=ilines[ii].strip().split(':')
        idict[iline[0]]=iline[1].strip()
        ii+=1
    
    #get number of parameters
    iline=ilines[ii].strip().split(':')
    nparam=int(iline[1].strip())
    idict[iline[0]]=nparam
    idict['model']=np.zeros(nparam)
    kk=int(ii+1)
    
    jj=0
    while jj<len(ilines)-kk:
        iline=ilines[jj+kk].strip().split()
        for ll in range(4):
            try:
                idict['model'][jj*4+ll]=float(iline[ll])
            except IndexError:
                pass
        jj+=1
            
    return idict


def compareIter(iterfn1,iterfn2,savepath=None):
    """
    compareIter will take the difference between two iteration and make a 
    difference iter file
    
    Inputs:
        iterfn1 = full path to iteration file 1
        iterfn2 = full path to iteration file 2
        savepath = path to save the difference iteration file, can be full or
                  just a directory
                  
    Outputs:
        diterfn = file name of iteration difference either:
            savepath/iterdiff##and##.iter
            or os.path.dirname(iterfn1,iterdiff##and##.iter)
            or savepath
    """

    #get number of iteration
    inum1=iterfn1[-7:-5]    
    inum2=iterfn2[-7:-5]    
    
    #make file name to save difference to
    if savepath==None:
        svdir=os.path.dirname(iterfn1)
        diterfn=os.path.join(svdir,
                              'iterdiff{0}and{1}.iter'.format(inum1,inum2))
    elif savepath.find('.')==-1:
        diterfn=os.path.join(savepath,
                              'iterdiff{0}and{1}.iter'.format(inum1,inum2))
    else:
        diterfn=savepath
    
    #read the iter files
    idict1=read2DIterFile(iterfn1)
    idict2=read2DIterFile(iterfn2)
    
    #calculate difference this way it will plot as red going conductive and
    #blues being a resistive change
    mdiff=-idict1['model']+idict2['model']
    nd=len(mdiff)
    
    ifid=file(iterfn1,'r')
    ilines=ifid.readlines()
    ifid.close()    
    
    #write iterfile
    dfid=file(diterfn,'w')
    ii=0
    while ilines[ii].find('Param')!=0:
        dfid.write(ilines[ii])
        ii+=1
    
    dfid.write('Param Count:        {0}\n'.format(nd))
    
    for jj in range(nd/4+1):
        for kk in range(4):
            try:
                dfid.write('   {0:+.6f}'.format(mdiff[4*jj+kk]))
                if kk==3:
                    dfid.write('\n')
            except IndexError:
                dfid.write('\n')
            
    dfid.close()
    
    return diterfn
        
def plot2DResponses(datafn,respfn=None,wlfn=None,maxcol=8,plottype='1',ms=4,
                    phaselimits=(-5,95),colormode='color',reslimits=None,
                    **kwargs):
    """
    plotResponse will plot the responses modeled from winglink against the 
    observed data.
    
    Inputs:
        respfn = full path to response file
        datafn = full path to data file
        wlfn = full path to a winglink data file used for a similar
                          inversion.  This will be plotted on the response
                          plots for comparison of fits.
        maxcol = maximum number of columns for the plot
        plottype = 'all' to plot all on the same plot
                   '1' to plot each respones in a different figure
                   station to plot a single station or enter as a list of 
                   stations to plot a few stations [station1,station2].  Does
                   not have to be verbatim but should have similar unique 
                   characters input pb01 for pb01cs in outputfile
    Outputs:
        used for interactive masking of points
        axlst = list of axes plotted
        errlst = list of errors that were plotted
        linelst = list of lines plotted
    """

    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt
    import mtpy.modeling.winglinktools as wlt
    from matplotlib.ticker import MultipleLocator
    
    
    plt.rcParams['font.size']=10
    
    try:
        dpi=kwargs['dpi']
    except KeyError:
        dpi=200
    if colormode=='color':
        #color for data
        cted=(0,0,1)
        ctmd=(1,0,0)
        mted='*'
        mtmd='*'
        
        #color for occam model
        ctem=(0,.6,.3)
        ctmm=(.9,0,.8)
        mtem='+'
        mtmm='+'
        
        #color for Wingling model
        ctewl=(0,.6,.8)
        ctmwl=(.8,.7,0)
        mtewl='x'
        mtmwl='x'
        
    elif colormode=='bw':
        #color for data
        cted=(0,0,0)
        ctmd=(0,0,0)
        mted='*'
        mtmd='v'
        
        #color for occam model
        ctem=(0.6,.6,.6)
        ctmm=(.6,.6,.6)
        mtem='+'
        mtmm='x'
        
        #color for Wingling model
        ctewl=(.3,.3,.3)
        ctmwl=(.3,.3,.3)    
        mtewl='|'
        mtmwl='_'
        
    if respfn!=None:
        #read in the data    
        rplst,stationlst,freq,title=read2DRespFile(respfn,datafn)
        #make a legend list for plotting
        legendlst=['$Obs_{xy}$','$Obs_{yx}$','$Mod_{xy}$','$Mod_{yx}$']
        plotresp=True
    else:
        rplst,stationlst,freq,title,theta=read2DdataFile(datafn)
        #make a legend list for plotting
        legendlst=['$Obs_{xy}$','$Obs_{yx}$']
        plotresp=False
    
    #boolean for adding winglink output to the plots 0 for no, 1 for yes
    addwl=0
    hspace=.15
    #read in winglink data file
    if wlfn!=None:
        addwl=1
        hspace=.25
        wld,wlrplst,wlplst,wlslst,wltlst=wlt.readOutputFile(wlfn)
        legendlst=['$Obs_{xy}$','$Obs_{yx}$','Occ_$Mod_{xy}$','Occ_$Mod_{yx}$',
                   'Wl_$Mod_{xy}$','Wl_$Mod_{yx}$']
        sdict=dict([(ostation,wlstation) for wlstation in wlslst 
                    for ostation in stationlst if wlstation.find(ostation)>=0])
    period=1./freq
    nf=len(period)
    
    nstations=len(stationlst)
    
    #plot all responses onto one plot
    if plottype=='all':
        maxcol=8         
        nrows=int(np.ceil(nstations/float(maxcol)))
        
        fig=plt.figure(1,[14,10],dpi=dpi)
        gs=gridspec.GridSpec(nrows,1,hspace=hspace,left=.05,right=.98)
        count=0
        for rr in range(nrows):
            g1=gridspec.GridSpecFromSubplotSpec(6,maxcol,subplot_spec=gs[rr],
                                                    hspace=.15,wspace=.05)
            count=rr*(maxcol)
            for cc in range(maxcol):
                rlst=[]
                try:
                    ii=count+cc
                    stationlst[ii]
                except IndexError:
                    break
                rmslst=np.hstack((rplst[ii]['resxy'][3],
                                       rplst[ii]['resyx'][3],
                                        rplst[ii]['phasexy'][3],
                                        rplst[ii]['phaseyx'][3]))
                rms=np.sqrt(np.sum(ms**2 for ms in rmslst)/len(rmslst))
                #plot resistivity
                axr=plt.Subplot(fig,g1[:4,cc])
                fig.add_subplot(axr)
                #cut out missing data points first
                rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
                ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
                r1=axr.loglog(period[rxy],10**rplst[ii]['resxy'][0][rxy],
                              ls=':',marker='s',ms=ms,color='b',mfc='b')
                r2=axr.loglog(period[ryx],10**rplst[ii]['resyx'][0][ryx],
                              ls=':',marker='o',ms=ms,color=ctmd,mfc=ctmd)
                if plotresp==True:
                    mrxy=[np.where(rplst[ii]['resxy'][2]!=0)[0]]
                    mryx=[np.where(rplst[ii]['resyx'][2]!=0)[0]]
                    r3=axr.loglog(period[mrxy],10**rplst[ii]['resxy'][2][mrxy],
                                  ls='--',marker='+', ms=2*ms,color=ctem,mfc=ctem)
                    r4=axr.loglog(period[mryx],10**rplst[ii]['resyx'][2][mryx],
                                  ls='--',marker='+',ms=2*ms,color=ctmm,mfc=ctmm)
                
                    rlst=[r1,r2,r3,r4]
                else:
                    rlst=[r1,r2]
                #plot phase
                axp=plt.Subplot(fig,g1[-2:,cc])
                fig.add_subplot(axp)
                #cut out missing data points first
                pxy=[np.where(rplst[ii]['phasexy'][0]!=0)[0]]
                pyx=[np.where(rplst[ii]['phaseyx'][0]!=0)[0]]
                axp.semilogx(period[pxy],rplst[ii]['phasexy'][0][pxy],
                             ls=':',marker='s',ms=ms,color='b',mfc='b')
                axp.semilogx(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                             ls=':',marker='o',ms=ms,color=ctmd,mfc=ctmd)
                if plotresp==True:
                    mpxy=[np.where(rplst[ii]['phasexy'][2]!=0)[0]]
                    mpyx=[np.where(rplst[ii]['phaseyx'][2]!=0)[0]]
                    axp.semilogx(period[mpxy],rplst[ii]['phasexy'][2][mpxy],
                                 ls='--',marker='+',ms=2*ms,color=ctem,mfc=ctem)
                    axp.semilogx(period[mpyx],rplst[ii]['phaseyx'][2][mpyx],
                                 ls='--',marker='+',ms=2*ms,color=ctmm,mfc=ctmm)
                
                #add in winglink responses
                if addwl==1:
                    try:
                        wlrms=wld[sdict[stationlst[ii]]]['rms']
                        axr.set_title(stationlst[ii]+'\n'+\
                                    'rms_occ, rms_wl= %.2f, %.2f' % (rms,wlrms),
                                     fontdict={'size':12,'weight':'bold'})
                        r5=axr.loglog(wld[sdict[stationlst[ii]]]['period'],
                                   wld[sdict[stationlst[ii]]]['modresxy'],
                                   ls='-.',marker='x',ms=2*ms,color=ctewl,
                                   mfc=ctewl)
                        r6=axr.loglog(wld[sdict[stationlst[ii]]]['period'],
                                   wld[sdict[stationlst[ii]]]['modresyx'],
                                   ls='-.',marker='x',ms=2*ms,color=ctmwl,
                                   mfc=ctmwl)
                        axp.semilogx(wld[sdict[stationlst[ii]]]['period'],
                                     wld[sdict[stationlst[ii]]]['modphasexy'],
                                     ls='-.',marker='x',ms=2*ms,color=ctewl,
                                     mfc=ctewl)
                        axp.semilogx(wld[sdict[stationlst[ii]]]['period'],
                                     wld[sdict[stationlst[ii]]]['modphaseyx'],
                                     ls='-.',marker='x',ms=2*ms,color=ctmwl,
                                     mfc=ctmwl)
                        rlst.append(r5[0])
                        rlst.append(r6[0])
                    except IndexError:
                        print 'Station not present'
                else:
                    if plotresp==True:
                        axr.set_title(stationlst[ii]+'; rms= %.2f' % rms,
                                      fontdict={'size':12,'weight':'bold'})
                    else:
                        axr.set_title(stationlst[ii],
                                      fontdict={'size':12,'weight':'bold'})
                
                #make plot nice with labels
                if cc==0 and rr==0:
                    fig.legend(rlst,legendlst,
                                loc='upper center',markerscale=2,
                                borderaxespad=.35,
                                labelspacing=.08,
                                handletextpad=.15,borderpad=.1,
                                ncol=len(rlst))
                axr.grid(True,alpha=.4)
                axr.set_xticklabels(['' for ii in range(10)])
                if cc>0:
                    axr.set_yticklabels(['' for ii in range(6)])
                    
                axp.set_ylim(phaselimits)
                if reslimits!=None:
                    axr.set_ylim(reslimits)
                axp.grid(True,alpha=.4)
                axp.yaxis.set_major_locator(MultipleLocator(30))
                axp.yaxis.set_minor_locator(MultipleLocator(5))
                
                if cc==0:
                    axr.set_ylabel('App. Res. ($\Omega \cdot m$)',
                                   fontdict={'size':12,'weight':'bold'})
                    axp.set_ylabel('Phase (deg)',
                                   fontdict={'size':12,'weight':'bold'})
                    axr.yaxis.set_label_coords(-.15,.5)
                    axp.yaxis.set_label_coords(-.15,.5)
        
                if cc>0:
                    axr.set_yticklabels(['' for ii in range(6)])
                    axp.set_yticklabels(['' for ii in range(6)])
                if rr==nrows-1:
                    axp.set_xlabel('Period (s)',
                                   fontdict={'size':12,'weight':'bold'})
                                   
    #---------------plot each respones in a different figure------------------
    elif plottype=='1':
        gs=gridspec.GridSpec(6,2,wspace=.05)
         
        

        for ii,station in enumerate(stationlst):
            
            rlst=[]
            llst=[]
            
            rmslst=np.hstack((rplst[ii]['resxy'][3],
                                       rplst[ii]['resyx'][3],
                                        rplst[ii]['phasexy'][3],
                                        rplst[ii]['phaseyx'][3]))
            rms=np.sqrt(np.sum(ms**2 for ms in rmslst)/len(rmslst))
            fig=plt.figure(ii+1,[9,10],dpi=dpi)
            plt.clf()
            
            #plot resistivity
            axr=fig.add_subplot(gs[:4,:])
            #cut out missing data points first
            rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
            ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
            
            #check to see if there is a xy component
            if len(rxy)>0:
                rte=axr.errorbar(period[rxy],10**rplst[ii]['resxy'][0][rxy],
                                   ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,
                                   color=cted,
                                   yerr=np.log(10)*rplst[ii]['resxy'][1][rxy]*\
                                   10**rplst[ii]['resxy'][0][rxy],
                                   ecolor=cted,picker=2)
                rlst.append(rte[0])
                llst.append('$Obs_{xy}$')
            else:
                pass
            
            #check to see if there is a yx component
            if len(ryx)>0:
                rtm=axr.errorbar(period[ryx],10**rplst[ii]['resyx'][0][ryx],
                                   ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,
                                   color=ctmd,
                                   yerr=np.log(10)*rplst[ii]['resyx'][1][ryx]*\
                                   10**rplst[ii]['resyx'][0][ryx],
                                   ecolor=ctmd,picker=2)
                rlst.append(rtm[0])
                llst.append('$Obs_{yx}$')
            else:
                pass                                
            
            if plotresp==True:
                mrxy=np.where(rplst[ii]['resxy'][2]!=0)[0]
                mryx=np.where(rplst[ii]['resyx'][2]!=0)[0]
                
                #check for the xy of model component
                if len(mrxy)>0:
                    r3=axr.errorbar(period[mrxy],10**rplst[ii]['resxy'][2][mrxy],
                                    ls='--',marker=mtem,ms=ms,mfc=ctem,mec=ctem,
                                    color=ctem,
                                    yerr=10**(rplst[ii]['resxy'][3][mrxy]*\
                                    rplst[ii]['resxy'][2][mrxy]/np.log(10)),
                                    ecolor=ctem)
                    rlst.append(r3[0])
                    llst.append('$Mod_{xy}$')
                else:
                    pass
                
                #check for the yx model component  of resisitivity
                if len(mryx)>0:
                    r4=axr.errorbar(period[mryx],10**rplst[ii]['resyx'][2][mryx],
                                    ls='--',marker=mtmm,ms=ms,mfc=ctmm,mec=ctmm,
                                    color=ctmm,
                                    yerr=10**(rplst[ii]['resyx'][3][mryx]*\
                                    rplst[ii]['resyx'][2][mryx]/np.log(10)),
                                    ecolor=ctmm)
                    rlst.append(r4[0])
                    llst.append('$Mod_{yx}$')
                                
            #plot phase
            axp=fig.add_subplot(gs[-2:,:],sharex=axr)
            
            #cut out missing data points first
            pxy=np.where(rplst[ii]['phasexy'][0]!=0)[0]
            pyx=np.where(rplst[ii]['phaseyx'][0]!=0)[0]

            if len(pxy)>0:
                pte=axp.errorbar(period[pxy],rplst[ii]['phasexy'][0][pxy],
                                   ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,
                                   color=cted,
                                   yerr=rplst[ii]['phasexy'][1][pxy],
                                    ecolor=cted,picker=1)
            else:
                pass
            
            if len(pyx)>0:
                ptm=axp.errorbar(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                                   ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,
                                   color=ctmd,
                                   yerr=rplst[ii]['phaseyx'][1][pyx],
                                    ecolor=ctmd,picker=1)
            else:
                pass
            
            if plotresp==True:
                mpxy=np.where(rplst[ii]['phasexy'][2]!=0)[0]
                mpyx=np.where(rplst[ii]['phaseyx'][2]!=0)[0]
                
                if len(mpxy)>0:
                    axp.errorbar(period[mpxy],rplst[ii]['phasexy'][2][mpxy],
                                 ls='--',marker=mtem,ms=ms,mfc=ctem,mec=ctem,
                                 color=ctem,yerr=rplst[ii]['phasexy'][3][mpxy],
                                 ecolor=ctem)
                else:
                    pass
                
                if len(mpyx)>0:
                    axp.errorbar(period[mpyx],rplst[ii]['phaseyx'][2][mpyx],
                                 ls='--',marker=mtmm,ms=ms,mfc=ctmm,mec=ctmm,
                                 color=ctmm,yerr=rplst[ii]['phaseyx'][3][mpyx],
                                 ecolor=ctmm)
                else:
                    pass
#                axp.semilogx(period[mpxy],rplst[ii]['phasexy'][2][mpxy],
#                             ls='--',marker='+',ms=2*ms,color=ctem,mfc=ctem)
#                axp.semilogx(period[mpyx],rplst[ii]['phaseyx'][2][mpyx],
#                             ls='--',marker='+',ms=2*ms,color=ctmm,mfc=ctmm)
                         
            #add in winglink responses
            if addwl==1:
                try:
                    wlrms=wld[sdict[station]]['rms']
                    axr.set_title(stationlst[ii]+'\n'+\
                                'rms_occ, rms_wl= %.2f, %.2f' % (rms,wlrms),
                                 fontdict={'size':12,'weight':'bold'})
                    for ww,wlstation in enumerate(wlslst):
#                        print station,wlstation
                        if wlstation.find(station)==0:
                            print station,wlstation
                            wlrpdict=wlrplst[ww]
                    
                    zrxy=[np.where(wlrpdict['resxy'][0]!=0)[0]]
                    zryx=[np.where(wlrpdict['resyx'][0]!=0)[0]]
                    
                     #plot winglink resistivity
                    r5=axr.loglog(wlplst[zrxy],wlrpdict['resxy'][1][zrxy],
                                  ls='-.',marker=mtewl,ms=5,color=ctewl,
                                  mfc=ctewl)
                    r6=axr.loglog(wlplst[zryx],wlrpdict['resyx'][1][zryx],
                                  ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                  mfc=ctmwl)
                    
                    #plot winglink phase
                    axp.semilogx(wlplst[zrxy],wlrpdict['phasexy'][1][zrxy],
                                 ls='-.',marker=mtewl,ms=5,color=ctewl,
                                 mfc=ctewl)
                    axp.semilogx(wlplst[zryx],wlrpdict['phaseyx'][1][zryx],
                                 ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                 mfc=ctmwl)
                    
                    rlst.append(r5[0])
                    rlst.append(r6[0])
                    llst.append('$WLMod_{xy}$')
                    llst.append('$WLMod_{yx}$')
                except IndexError:
                    print 'Station not present'
            else:
                axr.set_title(stationlst[ii]+'; rms= %.2f' % rms,
                              fontdict={'size':16,'weight':'bold'})
            
                            
            axr.set_xscale('log')
            axp.set_xscale('log')
            axr.set_yscale('log')
            axr.grid(True,alpha=.4)
#            axr.set_xticklabels(['' for ii in range(10)])
            axp.set_ylim(phaselimits)
            if reslimits!=None:
                axr.set_ylim(10**reslimits[0],10**reslimits[1])
            axp.grid(True,alpha=.4)
            axp.yaxis.set_major_locator(MultipleLocator(10))
            axp.yaxis.set_minor_locator(MultipleLocator(1))
            plt.setp(axr.xaxis.get_ticklabels(),visible=False)
            
            axr.set_ylabel('App. Res. ($\Omega \cdot m$)',
                           fontdict={'size':12,'weight':'bold'})
            axp.set_ylabel('Phase (deg)',
                           fontdict={'size':12,'weight':'bold'})
            axp.set_xlabel('Period (s)',fontdict={'size':12,'weight':'bold'})
            axr.legend(rlst,llst,
                       loc=2,markerscale=1,borderaxespad=.05,
                       labelspacing=.08,
                       handletextpad=.15,borderpad=.05,prop={'size':12})
            axr.yaxis.set_label_coords(-.07,.5)
            axp.yaxis.set_label_coords(-.07,.5)
            
    #---Plot single or subset of stations-------------------------------------
    else:
        pstationlst=[]

        if type(plottype) is not list:
            plottype=[plottype]
        for ii,station in enumerate(stationlst):
            for pstation in plottype:
                if station.find(pstation)>=0:
#                    print 'plotting ',station
                    pstationlst.append(ii)
        if addwl==1:
            pwlstationlst=[]
            for ww,wlstation in enumerate(wlslst):
                for pstation in plottype:
                    if wlstation.find(pstation)>=0:
#                        print 'plotting ',wlstation
                        pwlstationlst.append(ww)  

        gs=gridspec.GridSpec(6,2,wspace=.05,left=.1,top=.93,bottom=.07)
        for jj,ii in enumerate(pstationlst):
            rlst=[]
            pstation=stationlst[ii]
            rmslst=np.hstack((rplst[ii]['resxy'][3],
                                       rplst[ii]['resyx'][3],
                                        rplst[ii]['phasexy'][3],
                                        rplst[ii]['phaseyx'][3]))
            rms=np.sqrt(np.sum(ms**2 for ms in rmslst)/len(rmslst))
            fig=plt.figure(ii+1,dpi=dpi)
            plt.clf()
            #plot resistivity
            #cut out missing data points first
            axr=fig.add_subplot(gs[:4,:])
            rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
            ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
            rte=axr.errorbar(period[rxy],10**rplst[ii]['resxy'][0][rxy],
                    ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,
                    color=cted,
                    yerr=np.log(10)*rplst[ii]['resxy'][1][rxy]*\
                        10**rplst[ii]['resxy'][0][rxy],
                    ecolor=cted,picker=2)
            rtm=axr.errorbar(period[ryx],10**rplst[ii]['resyx'][0][ryx],
                    ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,
                    color=ctmd,
                    yerr=np.log(10)*rplst[ii]['resyx'][1][ryx]*\
                        10**rplst[ii]['resyx'][0][ryx],
                    ecolor=ctmd,picker=2)
#            r1=axr.loglog(period[rxy],10**rplst[ii]['resxy'][0][rxy],
#                          ls=':',marker='s',ms=ms,color=cted,mfc=cted)
#            r2=axr.loglog(period[ryx],10**rplst[ii]['resyx'][0][ryx],
#                          ls=':',marker='o',ms=ms,color=ctmd,mfc=ctmd)
            if plotresp==True:
                mrxy=[np.where(rplst[ii]['resxy'][2]!=0)[0]]
                mryx=[np.where(rplst[ii]['resyx'][2]!=0)[0]]
                r3=axr.errorbar(period[mrxy],10**rplst[ii]['resxy'][2][mrxy],
                                ls='--',marker=mtem,ms=ms,mfc=ctem,mec=ctem,
                                color=ctem,
                                yerr=10**(rplst[ii]['resxy'][3][mrxy]*\
                                rplst[ii]['resxy'][2][mrxy]/np.log(10)),
                                ecolor=ctem)
                r4=axr.errorbar(period[mryx],10**rplst[ii]['resyx'][2][mryx],
                                ls='--',marker=mtmm,ms=ms,mfc=ctmm,mec=ctmm,
                                color=ctmm,
                                yerr=10**(rplst[ii]['resyx'][3][mryx]*\
                                rplst[ii]['resyx'][3][mryx]/np.log(10)),
                                ecolor=ctmm)
#                r3=axr.loglog(period[mrxy],10**rplst[ii]['resxy'][2][mrxy],
#                              ls='--',marker='+', ms=2*ms,color=ctem,mfc=ctem)
#                r4=axr.loglog(period[mryx],10**rplst[ii]['resyx'][2][mryx],
#                              ls='--',marker='+',ms=2*ms,color=ctmm,mfc=ctmm)
            
                rlst=[rte[0],rtm[0],r3[0],r4[0]]
            else:
                rlst=[rte[0],rtm[0]]
                                
            #plot phase
            axp=fig.add_subplot(gs[-2:,:],sharex=axr)
            #cut out missing data points first
            pxy=[np.where(rplst[ii]['phasexy'][0]!=0)[0]]
            pyx=[np.where(rplst[ii]['phaseyx'][0]!=0)[0]]
            pte=axp.errorbar(period[pxy],rplst[ii]['phasexy'][0][pxy],
                       ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,color=cted,
                       yerr=rplst[ii]['phasexy'][1][pxy],ecolor=cted,picker=1)
            ptm=axp.errorbar(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                    ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,color=ctmd,
                    yerr=rplst[ii]['phaseyx'][1][pyx],ecolor=ctmd,picker=1)
#            axp.semilogx(period[pxy],rplst[ii]['phasexy'][0][pxy],
#                         ls=':',marker='s',ms=ms,color=cted,mfc=cted)
#            axp.semilogx(period[pyx],rplst[ii]['phaseyx'][0][pyx],
#                         ls=':',marker='o',ms=ms,color=ctmd,mfc=ctmd)
            if plotresp==True:
                mpxy=[np.where(rplst[ii]['phasexy'][2]!=0)[0]]
                mpyx=[np.where(rplst[ii]['phaseyx'][2]!=0)[0]]
                
                axp.errorbar(period[mpxy],rplst[ii]['phasexy'][2][mpxy],
                            ls='--',marker=mtem,ms=ms,mfc=ctem,mec=ctem,color=ctem,
                            yerr=rplst[ii]['phasexy'][3][mpxy],ecolor=ctem)
                axp.errorbar(period[mpyx],rplst[ii]['phaseyx'][2][mpyx],
                            ls='--',marker=mtmm,ms=ms,mfc=ctmm,mec=ctmm,color=ctmm,
                            yerr=rplst[ii]['phaseyx'][3][mpyx],ecolor=ctmm)
#                axp.semilogx(period[mpxy],rplst[ii]['phasexy'][2][mpxy],
#                             ls='--',marker='+',ms=2*ms,color=ctem,mfc=ctem)
#                axp.semilogx(period[mpyx],rplst[ii]['phaseyx'][2][mpyx],
#                             ls='--',marker='+',ms=2*ms,color=ctmm,mfc=ctmm)
                         
            #add in winglink responses
            if addwl==1:
                try:
                    wlrms=wld[sdict[station]]['rms']
                    print 'plotting WL station: ', sdict[pstation]
                    axr.set_title(pstation+'\n'+\
                                'rms_occ, rms_wl= %.2f, %.2f' % (rms,wlrms),
                                 fontdict={'size':12,'weight':'bold'})
                    wlrpdict=wlrplst[pwlstationlst[jj]]
                    zrxy=[np.where(wlrpdict['resxy'][0]!=0)[0]]
                    zryx=[np.where(wlrpdict['resyx'][0]!=0)[0]]
                    
                    #plot winglink Resistivity
                    r5=axr.loglog(wlplst[zrxy],wlrpdict['resxy'][1][zrxy],
                                  ls='-.',marker=mtewl,ms=5,color=ctewl,
                                  mfc=ctewl)
                    r6=axr.loglog(wlplst[zryx],wlrpdict['resyx'][1][zryx],
                                  ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                  mfc=ctmwl)
                    #plot winglink phase
                    axp.semilogx(wlplst[zrxy],wlrpdict['phasexy'][1][zrxy],
                                 ls='-.',marker=mtewl,ms=5,color=ctewl,
                                 mfc=ctewl)
                    axp.semilogx(wlplst[zryx],wlrpdict['phaseyx'][1][zryx],
                                 ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                 mfc=ctmwl)
                    rlst.append(r5[0])
                    rlst.append(r6[0])
                except IndexError:
                    print 'Station not present'
            else:
                if plotresp==True:
                    axr.set_title(pstation+'; rms= %.2f' % rms,
                                  fontdict={'size':16,'weight':'bold'})
                else:
                    axr.set_title(pstation,
                                  fontdict={'size':16,'weight':'bold'})
                       
            
            axr.set_xscale('log')
            axr.set_yscale('log')
            axp.set_xscale('log') 
            plt.setp(axr.xaxis.get_ticklabels(),visible=False)                 
            axr.grid(True,alpha=.4)
#            axr.set_xticklabels(['' for ii in range(10)])
            axp.set_ylim(phaselimits)
            if reslimits!=None:
                axr.set_ylim(reslimits)
            axp.grid(True,alpha=.4)
            axp.yaxis.set_major_locator(MultipleLocator(10))
            axp.yaxis.set_minor_locator(MultipleLocator(1))
            
            axr.set_ylabel('App. Res. ($\Omega \cdot m$)',
                           fontdict={'size':12,'weight':'bold'})
            axp.set_ylabel('Phase (deg)',
                           fontdict={'size':12,'weight':'bold'})
            axp.set_xlabel('Period (s)',fontdict={'size':12,'weight':'bold'})
            axr.legend(rlst,legendlst,
                       loc=2,markerscale=2,borderaxespad=.05,
                       labelspacing=.08,
                       handletextpad=.15,borderpad=.05,prop={'size':12})
            axr.yaxis.set_label_coords(-.075,.5)
            axp.yaxis.set_label_coords(-.075,.5)
            
#    return axlst,linelst,errlst
    
def plotTipper(datafile,):
    pass
    
def plotAllResponses(datafile,station,fignum=1):
    """
    Plot all the responses of occam inversion from data file.  This assumes
    the response curves are in the same folder as the datafile.

    Input:
        datafile = full path to occam data file
        
    Output:
        Plot
    
    """    

    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator
    
    rpath=os.path.dirname(datafile)
    
    gs=gridspec.GridSpec(6,2,wspace=.20)
    
    plt.rcParams['font.size']=int(7)
    plt.rcParams['figure.subplot.left']=.08
    plt.rcParams['figure.subplot.right']=.98
    plt.rcParams['figure.subplot.bottom']=.1
    plt.rcParams['figure.subplot.top']=.92


    rlst=[os.path.join(rpath,rfile) for rfile in os.listdir(rpath) 
            if rfile.find('.resp')>0]
    
    nresp=len(rlst)
    
    colorlst=[(cc,0,1-cc) for cc in np.arange(0,1,1./nresp)]
    fig=plt.figure(fignum,[7,8],dpi=200)
    plt.clf()
    axrte=fig.add_subplot(gs[:4,0])
    axrtm=fig.add_subplot(gs[:4,1])
    axpte=fig.add_subplot(gs[-2:,0])
    axptm=fig.add_subplot(gs[-2:,1])
    rmstelst=[]
    rmstmlst=[]
    rmstestr=[]
    rmstmstr=[]
    #read responses
    for jj,rfile in enumerate(rlst):
        rplst,stationlst,freq,title=read2DRespFile(os.path.join(rpath,rfile),
                                                 datafile)
        ii=np.where(np.array(stationlst)==station)[0][0]
        
        period=1./freq
        
        rmslstte=np.hstack((rplst[ii]['resxy'][3],
                            rplst[ii]['phasexy'][3]))
        rmslsttm=np.hstack((rplst[ii]['resyx'][3],
                            rplst[ii]['phaseyx'][3]))
        rmste=np.sqrt(np.sum(ms**2 for ms in rmslstte)/len(rmslstte))
        rmstm=np.sqrt(np.sum(ms**2 for ms in rmslsttm)/len(rmslsttm))
        rmstelst.append('%d rms=%.3f ' % (jj,rmste))
        rmstmlst.append('%d rms=%.3f ' % (jj,rmstm))
        rmstestr.append(rmste)
        rmstmstr.append(rmstm)
        #plot resistivity
        
        
        if jj==0:
            #cut out missing data points first
            rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
            ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
            r1,=axrte.loglog(period[rxy],10**rplst[ii]['resxy'][0][rxy],
                          ls=':',marker='s',ms=4,color='k',mfc='k')
            r2,=axrtm.loglog(period[ryx],10**rplst[ii]['resyx'][0][ryx],
                          ls=':',marker='o',ms=4,color='k',mfc='k')
            rlstte=[r1]
            rlsttm=[r2]
    
        mrxy=[np.where(rplst[ii]['resxy'][2]!=0)[0]]
        mryx=[np.where(rplst[ii]['resyx'][2]!=0)[0]]
        r3,=axrte.loglog(period[mrxy],10**rplst[ii]['resxy'][2][mrxy],
                        ls='-',color=colorlst[jj])
        r4,=axrtm.loglog(period[mryx],10**rplst[ii]['resyx'][2][mryx],
                        ls='-',color=colorlst[jj])
    
        rlstte.append(r3)
        rlsttm.append(r4)
                            
        #plot phase
        #cut out missing data points first
        pxy=[np.where(rplst[ii]['phasexy'][0]!=0)[0]]
        pyx=[np.where(rplst[ii]['phaseyx'][0]!=0)[0]]
        
        if jj==0:            
            axpte.semilogx(period[pxy],rplst[ii]['phasexy'][0][pxy],
                         ls=':',marker='s',ms=4,color='k',mfc='k')
            axptm.semilogx(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                         ls=':',marker='o',ms=4,color='k',mfc='k')
                         
        mpxy=[np.where(rplst[ii]['phasexy'][2]!=0)[0]]
        mpyx=[np.where(rplst[ii]['phaseyx'][2]!=0)[0]]
        axpte.semilogx(period[mpxy],rplst[ii]['phasexy'][2][mpxy],
                     ls='-',color=colorlst[jj])
        axptm.semilogx(period[mpyx],rplst[ii]['phaseyx'][2][mpyx],
                     ls='-',color=colorlst[jj])
    
#    teh,tel=axrte.get_legend_handles_labels()                 
#    axrte.legend(rlstte,rmstelst,loc=2,markerscale=2,borderaxespad=.05,
#               labelspacing=.08,
#               handletextpad=.15,borderpad=.05)
    
#    tmh,tml=axrtm.get_legend_handles_labels() 
#    axrtm.legend(rlsttm,rmstmlst,loc=2,markerscale=2,borderaxespad=.05,
#               labelspacing=.08,
#               handletextpad=.15,borderpad=.05)
                   
    axrte.grid(True,alpha=.4)
    axrtm.grid(True,alpha=.4)
    
    
    axrtm.set_xticklabels(['' for ii in range(10)])
    axrte.set_xticklabels(['' for ii in range(10)])
    #axpte.set_ylim(-10,120)
    
    rmstestr=np.median(np.array(rmstestr)[1:])
    rmstmstr=np.median(np.array(rmstmstr)[1:])
    axrte.set_title('TE rms={0:.2f}'.format(rmstestr),
                    fontdict={'size':10,'weight':'bold'})
    axrtm.set_title('TM rms={0:.2f}'.format(rmstmstr),
                    fontdict={'size':10,'weight':'bold'})
    
    axpte.grid(True,alpha=.4)
    axpte.yaxis.set_major_locator(MultipleLocator(10))
    axpte.yaxis.set_minor_locator(MultipleLocator(1))
    
    axrte.set_ylabel('App. Res. ($\Omega \cdot m$)',
                   fontdict={'size':10,'weight':'bold'})
    axpte.set_ylabel('Phase (deg)',
                   fontdict={'size':10,'weight':'bold'})
    axpte.set_xlabel('Period (s)',fontdict={'size':10,'weight':'bold'})

    axrte.yaxis.set_label_coords(-.08,.5)
    axpte.yaxis.set_label_coords(-.08,.5)
    
    axrtm.set_xticklabels(['' for ii in range(10)])
#    axptm.set_ylim(-10,120)
    axptm.grid(True,alpha=.4)
    axptm.yaxis.set_major_locator(MultipleLocator(10))
    axptm.yaxis.set_minor_locator(MultipleLocator(1))
    
    axrtm.set_ylabel('App. Res. ($\Omega \cdot m$)',
                   fontdict={'size':12,'weight':'bold'})
    axptm.set_ylabel('Phase (deg)',
                   fontdict={'size':12,'weight':'bold'})
    axptm.set_xlabel('Period (s)',fontdict={'size':12,'weight':'bold'})

    axrtm.yaxis.set_label_coords(-.08,.5)
    axptm.yaxis.set_label_coords(-.08,.5)
    plt.suptitle(station,fontsize=12,fontweight='bold')
    plt.show()
    
    
def plot2DModel(iterfile,meshfile=None,inmodelfile=None,datafile=None,
                xpad=1.0,ypad=6.0,mpad=0.5,spad=3.0,ms=60,stationid=None,
                fdict={'size':8,'rotation':60,'weight':'normal'},
                dpi=300,ylimits=None,xminorticks=5,yminorticks=1,
                climits=(0,4), cmap='jet_r',fs=8,femesh='off',
                regmesh='off',aspect='auto',title='on',meshnum='off',
                blocknum='off',blkfdict={'size':3},fignum=1,
                plotdimensions=(10,10),grid='off',yscale='km'):
    """
    plotModel will plot the model output by occam in the iteration file.
    
    Inputs:
        iterfile = full path to the iteration file that you want to plot
        
        meshfile = full path to mesh file (the forward modeling mesh).  If 
                    none it will look for a file with mesh in the name.
        
        inmodelfile = full path to the INMODEL file (regularization mesh).
                      If none it will look for a file with inmodel in the name.
        
        datafile = full path to data file.  If none is input it will use the
                    data file found in the iteration file.
        
        xpad = padding in the horizontal direction of model
        
        ypad = padding the in the vertical direction of the top of the model
               to fit the station names and markers
               
        mpad = marker pad to fit right at the surface, haven't found a better
               way of doing this automatically yet
               
        spad = padding of station names away from the top of the model, this
                is kind of awkward at the moment especially if you zoom into 
                the model, it usually looks retarded and doesn't fit
                
        ms = marker size in ambiguous points
        
        stationid = index of station names to plot -> ex. pb01sdr would be 
                    stationid=(0,4) to plot pb01
                    
        fdict = font dictionary for the station names, can have keys:
                'size' = font size
                'rotation' = angle of rotation (deg) of font
                'weight' = weight of font 
                'color' = color of font
                'style' = style of font ex. 'italics'
                
        plotdimensions = x-y dimensions of the figure (10,10) in inches
                
        dpi = dot per inch of figure, should be 300 for publications
        
        ylimits = limits of depth scale (km). ex, ylimits=(0,30)
        
        xminorticks = location of minor tick marks for the horizontal axis
        
        yminorticks = location of minor tick marks for vertical axis
        
        climits = limits of log10(resistivity). ex. climits=(0,4)
        
        cmap = color map to plot the model image
        
        fs = font size of axis labels
        
        femesh = 'on' to plot finite element forward modeling mesh (black)
        
        regmesh = 'on' to plot regularization mesh (blue)
        
        aspect = aspect ratio of the figure, depends on your line length and
                the depth you want to investigate
        
        title = 'on' to put the RMS and Roughness as the title, or input a 
                string that will be added to the RMS and roughness, or put 
                None to not put a title on the plot and print out RMS and 
                roughness
        
        meshnum = 'on' to plot FE mesh block numbers
        
        fignum = figure number to plot to
        
        blocknum = 'on' to plot numbers on the regularization blocks
        
        blkfdict = font dictionary for the numbering of regularization blocks
        
        grid = major for major ticks grid
               minor for a grid of the minor ticks
               both for a grid with major and minor ticks
        
        yscale = 'km' for depth in km or 'm' for depth in meters
    """
        
    
    #get directory path of inversion folder
    invpath=os.path.dirname(iterfile)    
    
    #read in iteration file
    idict=read2DIterFile(iterfile)    
    
    #get meshfile if none is provides assuming the mesh file is named with
    #mesh
    if meshfile==None:
        meshfile=os.path.join(invpath,'MESH')
        if os.path.isfile(meshfile)==False:
            for ff in os.listdir(invpath):
                if ff.lower().find('mesh')>=0:
                    meshfile=os.path.join(invpath,ff)
            if os.path.isfile(meshfile)==False:
                raise NameError('Could not find a mesh file, input manually')
    
    #get inmodelfile if none is provides assuming the mesh file is named with
    #inmodel
    if inmodelfile==None:
        inmodelfile=os.path.join(invpath,'INMODEL')
        if os.path.isfile(inmodelfile)==False:
            for ff in os.listdir(invpath):
                if ff.lower().find('inmodel')>=0:
                    inmodelfile=os.path.join(invpath,ff)
            if os.path.isfile(inmodelfile)==False:
                raise NameError('Could not find a model file, input manually')
                
    #get datafile if none is provides assuming the mesh file is named with
    #.dat
    if datafile==None:
        datafile=idict['Data File']
        if datafile.find(os.sep)==-1:
            datafile=os.path.join(invpath,datafile)
        if os.path.isfile(datafile)==False:
            for ff in os.listdir(invpath):
                if ff.lower().find('.dat')>=0:
                    datafile=os.path.join(invpath,ff)
            if os.path.isfile(datafile)==False:
                raise NameError('Could not find a data file, input manually')
    
    if yscale=='km':
        dfactor=1000.
        pfactor=1.0
    elif yscale=='m':
        dfactor=1.
        pfactor=1000.
    else:
        dfactor=1000.
        pfactor=1.0
    #read in data file
    print 'Reading data from: ',datafile
    rplst,slst,freq,datatitle,theta=read2DdataFile(datafile)
    
    #read in MESH file
    print 'Reading mesh from: ',meshfile
    hnode,vnode,freeparam=read2Dmesh(meshfile)
    
    #read in INMODEL
    print 'Reading model from: ',inmodelfile
    cr,cc,header=read2DInmodel(inmodelfile)
    bndgoff=float(header['BINDING OFFSET'])/dfactor
    
    #make a meshgrid 
    X,Y=np.meshgrid(hnode,vnode)
    
    cr=np.array(cr)
    
    nc=len(cr)
    assert len(cr)==len(cc)
    
    resmodel=np.zeros((vnode.shape[0],hnode.shape[0]))
    mm=0
    for ii in range(nc):
        #get the number of layers to combine
        #this index will be the first index in the vertical direction
        ny1=cr[:ii,0].sum()
        #the second index  in the vertical direction
        ny2=ny1+cr[ii][0]
        #make the list of amalgamated columns an array for ease
        lc=np.array(cc[ii])
        #loop over the number of amalgamated blocks
        for jj in range(len(cc[ii])):
            #get first in index in the horizontal direction
            nx1=lc[:jj].sum()
            #get second index in horizontal direction
            nx2=nx1+lc[jj]
            #put the apporpriate resistivity value into all the amalgamated model
            #blocks of the regularization grid into the forward model grid
            resmodel[ny1:ny2,nx1:nx2]=idict['model'][mm]
            mm+=1
    
    #make some arrays for plotting the model
    
    plotx=np.array([hnode[:ii+1].sum() for ii in range(len(hnode)-1)])/dfactor
    ploty=np.array([vnode[:ii+1].sum() for ii in range(len(vnode)-1)])/dfactor
    
    #center the grid onto the station coordinates
    x0=bndgoff-plotx[cc[0][0]]
    plotx=plotx+x0
    
    #flip the arrays around for plotting purposes
    #plotx=plotx[::-1] and make the first layer start at zero
    ploty=ploty[::-1]-ploty[0]
    
    #make a mesh grid to plot in the model coordinates
    x,y=np.meshgrid(plotx,ploty)
    
    #flip the resmodel upside down so that the top is the stations
    resmodel=np.flipud(resmodel)
    
    
    plt.rcParams['font.size']=int(dpi/40.)
    plt.rcParams['figure.subplot.left']=.08
    plt.rcParams['figure.subplot.right']=.99
    plt.rcParams['figure.subplot.bottom']=.1
    plt.rcParams['figure.subplot.top']=.92
    plt.rcParams['figure.subplot.wspace']=.01
    #plot the model
    fig=plt.figure(fignum,plotdimensions,dpi=dpi)
    plt.clf()
    ax=fig.add_subplot(1,1,1,aspect=aspect)
    
    ax.pcolormesh(x,y,resmodel,cmap=cmap,vmin=climits[0],vmax=climits[1])
    #ax.set_ylim(ploty[0],ploty[-1]-2.0)
    
    cbx=make_axes(ax,shrink=.8,pad=.01)
    cb=ColorbarBase(cbx[0],cmap=cmap,norm=Normalize(vmin=climits[0],
                    vmax=climits[1]))
    cb.set_label('Resistivity ($\Omega \cdot$m)',
                 fontdict={'size':fs,'weight':'bold'})
    cb.set_ticks(np.arange(int(climits[0]),int(climits[1])+1))
    cb.set_ticklabels(['10$^{0}$'.format(nn) for nn in 
                        np.arange(int(climits[0]),int(climits[1])+1)])
    
    offsetlst=[]
    for rpdict in rplst:
        #plot the station marker
        ax.scatter(rpdict['offset']/dfactor,-mpad*pfactor,marker='v',c='k',
                   s=ms)
        #put station id onto station marker
        #if there is a station id index
        if stationid!=None:
            ax.text(rpdict['offset']/dfactor,-spad*pfactor,
                    rpdict['station'][stationid[0]:stationid[1]],
                    horizontalalignment='center',
                    verticalalignment='baseline',
                    fontdict=fdict)
        #otherwise put on the full station name found form data file
        else:
            ax.text(rpdict['offset']/dfactor,-spad*pfactor,
                    rpdict['station'],
                    horizontalalignment='center',
                    verticalalignment='baseline',
                    fontdict=fdict)
        offsetlst.append(rpdict['offset']/dfactor)
    
    #set the initial limits of the plot to be square about the profile line  
    if ylimits==None:  
        ax.set_ylim(abs(max(offsetlst)-min(offsetlst))/dfactor,-ypad*pfactor)
    else:
        ax.set_ylim(ylimits[1]*pfactor,(ylimits[0]-ypad)*pfactor)
    ax.set_xlim(min(offsetlst)-(xpad*pfactor),
                 (max(offsetlst)+(xpad*pfactor)))
    #set the axis properties
    ax.xaxis.set_minor_locator(MultipleLocator(xminorticks*pfactor))
    ax.yaxis.set_minor_locator(MultipleLocator(yminorticks*pfactor))
    if yscale=='km':
        ax.set_xlabel('Horizontal Distance (km)',
                      fontdict={'size':fs,'weight':'bold'})
        ax.set_ylabel('Depth (km)',fontdict={'size':fs,'weight':'bold'})
    elif yscale=='m':
        ax.set_xlabel('Horizontal Distance (m)',
                      fontdict={'size':fs,'weight':'bold'})
        ax.set_ylabel('Depth (m)',fontdict={'size':fs,'weight':'bold'})
    
    #put a grid on if one is desired    
    if grid=='major':
        ax.grid(alpha=.3,which='major')
    if grid=='minor':
        ax.grid(alpha=.3,which='minor')
    if grid=='both':
        ax.grid(alpha=.3,which='both')
    else:
        pass
    
    #set title as rms and roughness
    if type(title) is str:
        if title=='on':
            titlestr=os.path.join(os.path.basename(os.path.dirname(iterfile)),
                                  os.path.basename(iterfile))
            ax.set_title(titlestr+': RMS {0:.2f}, Roughness={1:.0f}'.format(
                     float(idict['Misfit Value']),
                     float(idict['Roughness Value'])),
                     fontdict={'size':fs+1,'weight':'bold'})
        else:
            ax.set_title(title+'; RMS {0:.2f}, Roughness={1:.0f}'.format(
                     float(idict['Misfit Value']),
                     float(idict['Roughness Value'])),
                     fontdict={'size':fs+1,'weight':'bold'})
    else:
        print 'RMS {0:.2f}, Roughness={1:.0f}'.format(
                     float(idict['Misfit Value']),
                     float(idict['Roughness Value'])) 
    
    #plot forward model mesh    
    if femesh=='on':
        for xx in plotx:
            ax.plot([xx,xx],[0,ploty[0]],color='k',lw=.5)
        for yy in ploty:
            ax.plot([plotx[0],plotx[-1]],[yy,yy],color='k',lw=.5)
    
    #plot the regularization mesh
    if regmesh=='on':
        linelst=[]
        for ii in range(nc):
            #get the number of layers to combine
            #this index will be the first index in the vertical direction
            ny1=cr[:ii,0].sum()
            #the second index  in the vertical direction
            ny2=ny1+cr[ii][0]
            #make the list of amalgamated columns an array for ease
            lc=np.array(cc[ii])
            yline=ax.plot([plotx[0],plotx[-1]],[ploty[-ny1],ploty[-ny1]],color='b',lw=.5)
            linelst.append(yline)
            #loop over the number of amalgamated blocks
            for jj in range(len(cc[ii])):
                #get first in index in the horizontal direction
                nx1=lc[:jj].sum()
                #get second index in horizontal direction
                nx2=nx1+lc[jj]
                try:
                    if ny1==0:
                        ny1=1
                    xline=ax.plot([plotx[nx1],plotx[nx1]],[ploty[-ny1],ploty[-ny2]],
                                  color='b',lw=.5)
                    linelst.append(xline)
                except IndexError:
                    pass
                
    ##plot the mesh block numbers
    if meshnum=='on':
        kk=1
        for yy in ploty[::-1]:
            for xx in plotx:
                ax.text(xx,yy,'{0}'.format(kk),fontdict={'size':3})
                kk+=1
                
    ##plot regularization block numbers
    if blocknum=='on':
        kk=1
        for ii in range(nc):
            #get the number of layers to combine
            #this index will be the first index in the vertical direction
            ny1=cr[:ii,0].sum()
            #the second index  in the vertical direction
            ny2=ny1+cr[ii][0]
            #make the list of amalgamated columns an array for ease
            lc=np.array(cc[ii])
            #loop over the number of amalgamated blocks
            for jj in range(len(cc[ii])):
                #get first in index in the horizontal direction
                nx1=lc[:jj].sum()
                #get second index in horizontal direction
                nx2=nx1+lc[jj]
                try:
                    if ny1==0:
                        ny1=1
                    #get center points of the blocks
                    yy=ploty[-ny1]-(ploty[-ny1]-ploty[-ny2])/2
                    xx=plotx[nx1]-(plotx[nx1]-plotx[nx2])/2
                    #put the number
                    ax.text(xx,yy,'{0}'.format(kk),fontdict=blkfdict,
                            horizontalalignment='center',
                            verticalalignment='center')
                    kk+=1
                except IndexError:
                    pass
                
    plt.show()
      
def plotPseudoSection(datafn,respfn=None,fignum=1,rcmap='jet_r',pcmap='jet',
                      rlim=((0,4),(0,4)),plim=((0,90),(0,90)),ml=2,
                      stationid=[0,4]):
    """
    plots a pseudo section of the data
    
    datafn = full path to data file
    respfn = full path to response file
    """
    
    if respfn!=None:
        rplst,slst,freq,title=read2DRespFile(respfn,datafn)
        nr=2
    else:
        rplst,slst,freq,title,thetal=read2DdataFile(datafn)
        nr=1
    ns=len(slst)
    nf=len(freq)
    ylimits=(1./freq.min(),1./freq.max())
#    print ylimits
    
    #make a grid for pcolormesh so you can have a log scale
    #get things into arrays for plotting
    offsetlst=np.zeros(ns)
    resxyarr=np.zeros((nf,ns,nr))    
    resyxarr=np.zeros((nf,ns,nr))    
    phasexyarr=np.zeros((nf,ns,nr))    
    phaseyxarr=np.zeros((nf,ns,nr))

    for ii,rpdict in enumerate(rplst):
        offsetlst[ii]=rpdict['offset']     
        resxyarr[:,ii,0]=rpdict['resxy'][0]
        resyxarr[:,ii,0]=rpdict['resyx'][0]
        phasexyarr[:,ii,0]=rpdict['phasexy'][0]
        phaseyxarr[:,ii,0]=rpdict['phaseyx'][0]
        if respfn!=None:
            resxyarr[:,ii,1]=rpdict['resxy'][2]
            resyxarr[:,ii,1]=rpdict['resyx'][2]
            phasexyarr[:,ii,1]=rpdict['phasexy'][2]
            phaseyxarr[:,ii,1]=rpdict['phaseyx'][2]
            
            
    #make a meshgrid for plotting
    #flip frequency so bottom corner is long period
    dgrid,fgrid=np.meshgrid(offsetlst,1./freq[::-1])

    #make list for station labels
    slabel=[slst[ss][stationid[0]:stationid[1]] for ss in range(0,ns,ml)]
    labellst=['$r_{TE-Data}$','$r_{TE-Model}$',
              '$r_{TM-Data}$','$r_{TM-Model}$',
              '$\phi_{TE-Data}$','$\phi_{TE-Model}$',
              '$\phi_{TM-Data}$','$\phi_{TM-Model}$']
    xloc=offsetlst[0]+abs(offsetlst[0]-offsetlst[1])/5
    yloc=1./freq[1]
    
    if respfn!=None:
        

        plt.rcParams['font.size']=7
        plt.rcParams['figure.subplot.bottom']=.09
        plt.rcParams['figure.subplot.top']=.96        
        
        fig=plt.figure(fignum,dpi=200)
        gs1=gridspec.GridSpec(2,2,left=0.06,right=.48,hspace=.1,wspace=.005)
        gs2=gridspec.GridSpec(2,2,left=0.52,right=.98,hspace=.1,wspace=.005)
        
#        ax1r=fig.add_subplot(2,4,1)
        ax1r=fig.add_subplot(gs1[0,0])
        ax1r.pcolormesh(dgrid,fgrid,np.flipud(resxyarr[:,:,0]),cmap=rcmap,
                       vmin=rlim[0][0],vmax=rlim[0][1])
        
#        ax2r=fig.add_subplot(2,4,2)
        ax2r=fig.add_subplot(gs1[0,1])
        ax2r.pcolormesh(dgrid,fgrid,np.flipud(resxyarr[:,:,1]),cmap=rcmap,
                       vmin=rlim[0][0],vmax=rlim[0][1])
                       
#        ax3r=fig.add_subplot(2,4,3)
        ax3r=fig.add_subplot(gs2[0,0])
        ax3r.pcolormesh(dgrid,fgrid,np.flipud(resyxarr[:,:,0]),cmap=rcmap,
                       vmin=rlim[1][0],vmax=rlim[1][1])
        
#        ax4r=fig.add_subplot(2,4,4)
        ax4r=fig.add_subplot(gs2[0,1])
        ax4r.pcolormesh(dgrid,fgrid,np.flipud(resyxarr[:,:,1]),cmap=rcmap,
                       vmin=rlim[1][0],vmax=rlim[1][1])

#        ax1p=fig.add_subplot(2,4,5)
        ax1p=fig.add_subplot(gs1[1,0])
        ax1p.pcolormesh(dgrid,fgrid,np.flipud(phasexyarr[:,:,0]),cmap=pcmap,
                       vmin=plim[0][0],vmax=plim[0][1])
        
#        ax2p=fig.add_subplot(2,4,6)
        ax2p=fig.add_subplot(gs1[1,1])
        ax2p.pcolormesh(dgrid,fgrid,np.flipud(phasexyarr[:,:,1]),cmap=pcmap,
                       vmin=plim[0][0],vmax=plim[0][1])
                       
#        ax3p=fig.add_subplot(2,4,7)
        ax3p=fig.add_subplot(gs2[1,0])
        ax3p.pcolormesh(dgrid,fgrid,np.flipud(phaseyxarr[:,:,0]),cmap=pcmap,
                       vmin=plim[1][0],vmax=plim[1][1])
        
#        ax4p=fig.add_subplot(2,4,8)
        ax4p=fig.add_subplot(gs2[1,1])
        ax4p.pcolormesh(dgrid,fgrid,np.flipud(phaseyxarr[:,:,1]),cmap=pcmap,
                       vmin=plim[1][0],vmax=plim[1][1])
        
        axlst=[ax1r,ax2r,ax3r,ax4r,ax1p,ax2p,ax3p,ax4p]
        
        for xx,ax in enumerate(axlst):
            ax.semilogy()
            ax.set_ylim(ylimits)
#            ax.xaxis.set_major_locator(MultipleLocator(ml))
            ax.xaxis.set_ticks(offsetlst[np.arange(0,ns,ml)])
            ax.xaxis.set_ticks(offsetlst,minor=True)
            ax.xaxis.set_ticklabels(slabel)
            ax.set_xlim(offsetlst.min(),offsetlst.max())
            if np.remainder(xx,2.0)==1:
                plt.setp(ax.yaxis.get_ticklabels(),visible=False)
                cbx=mcb.make_axes(ax,shrink=.7,pad=.015)
                if xx<4:
                    if xx==1:
                        cb=mcb.ColorbarBase(cbx[0],cmap=rcmap,
                                        norm=Normalize(vmin=rlim[0][0],
                                                       vmax=rlim[0][1]))
#                        cb.set_label('Resistivity ($\Omega \cdot$m)',
#                                     fontdict={'size':9})
                    if xx==3:
                        cb=mcb.ColorbarBase(cbx[0],cmap=rcmap,
                                        norm=Normalize(vmin=rlim[1][0],
                                                       vmax=rlim[1][1]))
                        cb.set_label('App. Res. ($\Omega \cdot$m)',
                                     fontdict={'size':9})
                else:
                    if xx==5:
                        cb=mcb.ColorbarBase(cbx[0],cmap=pcmap,
                                        norm=Normalize(vmin=plim[0][0],
                                                       vmax=plim[0][1]))
#                        cb.set_label('Phase (deg)',fontdict={'size':9})
                    if xx==7:
                        cb=mcb.ColorbarBase(cbx[0],cmap=pcmap,
                                        norm=Normalize(vmin=plim[1][0],
                                                       vmax=plim[1][1]))
                        cb.set_label('Phase (deg)',fontdict={'size':9})
            ax.text(xloc,yloc,labellst[xx],
                    fontdict={'size':10},
                    bbox={'facecolor':'white'},
                    horizontalalignment='left',
                    verticalalignment='top')
            if xx==0 or xx==4:
                ax.set_ylabel('Period (s)',
                              fontdict={'size':10,'weight':'bold'})
            if xx>3:
                ax.set_xlabel('Station',fontdict={'size':10,'weight':'bold'})
            
                
        plt.show()
        
def plotDepthModel(iterfn,meshfn,slst,lm,fignum=1,dpi=300,depth=10000,
                   stations=None,yscale='log'):
    """
    will plot a depth section as a line for the block numbers given by slst and
    the layer multiplier lm
    """
                       
    idict=read2DIterFile(iterfn)
    harr,varr,marr=read2Dmesh(meshfn)
    
    v=np.array([varr[0:ii+1].sum() for ii in range(len(varr))])
#    print varr
    
    nv=len(np.where(v<depth)[0])

    v=v[::-1]
    
    fig=plt.figure(fignum,dpi=dpi)
    plt.clf()
    ax=fig.add_subplot(1,1,1)
    
    rholst=[]
    for ss in slst:
        ilst=np.arange(nv)*lm+(ss-1)
        rho=idict['model'][ilst]
        if yscale=='linear':
            p1,=ax.semilogx(10**(rho[::-1]),v[len(v)-len(ilst):],ls='steps-')
        elif yscale=='log':
            p1,=ax.loglog(10**(rho[::-1]),v[len(v)-len(ilst):],ls='steps-')
        rholst.append(p1)
    ax.set_ylim(depth,varr.min())
    if stations==None:
        ax.legend(rholst,np.arange(len(rholst)),loc=0)
    else:
        ax.legend(rholst,stations,loc=0)
    ax.set_ylabel('Depth (m)',fontdict={'size':8,'weight':'bold'})
    ax.set_xlabel('Resistivity ($\Omega \cdot$m)',fontdict={'size':8,'weight':'bold'})
    ax.grid(True,alpha=.3,which='both')
        
        
def plotL2Curve(invpath,fnstem=None,fignum=1,dpi=300):
    """
    PlotL2Curve will plot the RMS vs iteration number for the given inversion 
    folder and roughness vs iteration number
    
    Inputs: 
        invpath = full path to the inversion folder where .iter files are
        fnstem = filename stem to look for in case multiple inversions were
                run in the same folder.  If none then searches for anything
                ending in .iter
    
    Outputs:
        rmsiter = array(3x#iterations) of rms, iteration and roughness
    """ 
    
    if fnstem==None:
        iterlst=[os.path.join(invpath,itfile) 
                for itfile in os.listdir(invpath) if itfile.find('.iter')>0]
    else:
        iterlst=[os.path.join(invpath,itfile) 
                for itfile in os.listdir(invpath) if itfile.find('.iter')>0 and
                itfile.find(fnstem)>0]
                
    nr=len(iterlst)
    
    rmsarr=np.zeros((nr,2))
    
    for itfile in iterlst:
        idict=read2DIterFile(itfile)
        ii=int(idict['Iteration'])
        rmsarr[ii,0]=float(idict['Misfit Value'])
        rmsarr[ii,1]=float(idict['Roughness Value'])

        plt.rcParams['font.size']=int(dpi/40.)
    plt.rcParams['figure.subplot.left']=.08
    plt.rcParams['figure.subplot.right']=.90
    plt.rcParams['figure.subplot.bottom']=.1
    plt.rcParams['figure.subplot.top']=.90
    plt.rcParams['figure.subplot.wspace']=.01
    
    fig=plt.figure(fignum,[6,5],dpi=dpi)
    plt.clf()
    #make a subplot for RMS vs Iteration
    ax1=fig.add_subplot(1,1,1)
    
    #plot the rms vs iteration
    l1,=ax1.plot(np.arange(1,nr,1),rmsarr[1:,0],'-k',lw=1,marker='d',ms=5)
    
    #plot the median of the RMS
    m1,=ax1.plot(np.arange(0,nr,1),np.repeat(np.median(rmsarr[1:,0]),nr),
                 '--r',lw=.75)
    
    #plot the mean of the RMS
    m2,=ax1.plot(np.arange(0,nr,1),np.repeat(np.mean(rmsarr[1:,0]),nr),
                 ls='--',color='orange',lw=.75)

    #make subplot for RMS vs Roughness Plot
    ax2=ax1.twiny()
    
    #plot the rms vs roughness 
    l2,=ax2.plot(rmsarr[1:,1],rmsarr[1:,0],'--b',lw=.75,marker='o',ms=7,
                 mfc='white')
    for ii,rms in enumerate(rmsarr[1:,0],1):
        ax2.text(rmsarr[ii,1],rms,'{0}'.format(ii),
                 horizontalalignment='center',
                 verticalalignment='center',
                 fontdict={'size':6,'weight':'bold','color':'blue'})
    
    #make a legend
    ax1.legend([l1,l2,m1,m2],['RMS','Roughness',
               'Median_RMS={0:.2f}'.format(np.median(rmsarr[1:,0])),
                'Mean_RMS={0:.2f}'.format(np.mean(rmsarr[1:,0]))],
                ncol=4,loc='upper center',columnspacing=.25,markerscale=.75,
                handletextpad=.15)
                
    #set the axis properties for RMS vs iteration
    ax1.yaxis.set_minor_locator(MultipleLocator(.1))
    ax1.xaxis.set_minor_locator(MultipleLocator(1))
    ax1.set_ylabel('RMS',fontdict={'size':8,'weight':'bold'})                                   
    ax1.set_xlabel('Iteration',fontdict={'size':8,'weight':'bold'})
    ax1.grid(alpha=.25,which='both')
    ax2.set_xlabel('Roughness',fontdict={'size':8,'weight':'bold',
                                         'color':'blue'})
    for t2 in ax2.get_xticklabels():
        t2.set_color('blue')
#    #plot the median of the RMS
#    m1,=ax2.plot(np.arange(0,nr,1),np.repeat(np.median(rmsarr[1:,0]),nr),
#                 '--r',lw=.75)
#    
#    #plot the mean of the RMS
#    m2,=ax2.plot(np.arange(0,nr,1),np.repeat(np.mean(rmsarr[1:,0]),nr),
#                 ls='--',color='orange',lw=.75)
    #set the axis properties for RMS vs iteration
#    ax2.yaxis.set_minor_locator(MultipleLocator(.1))
#    ax2.xaxis.set_minor_locator(MultipleLocator(1))
#    ax2.set_ylabel('RMS',fontdict={'size':8,'weight':'bold'})                                   
#    ax2.set_xlabel('Roughness',fontdict={'size':8,'weight':'bold'})
#    ax2.grid(alpha=.25,which='both')
                
    
    plt.show()


def getdatetime():


    return time.asctime(time.gmtime())




def makestartfiles(parameter_dict):

    read_datafile(parameter_dict)

    parameter_dict['n_sideblockelements'] = 7
    parameter_dict['n_bottomlayerelements'] = 4

    parameter_dict['itform'] = 'not specified'
    parameter_dict['description'] = 'N/A'

    parameter_dict['datetime'] = getdatetime()
    

    parameter_dict['iruf'] = 1
    parameter_dict['idebug'] = 1
    parameter_dict['nit'] = 0
    parameter_dict['pmu'] = 5.0
    parameter_dict['rlast'] = 1.0E+07
    parameter_dict['tobt'] = 100.
    parameter_dict['ifftol'] = 0
    
    blocks_elements_setup(parameter_dict)
    
    get_model_setup(parameter_dict)
    
    writemeshfile(parameter_dict)
    writemodelfile(parameter_dict)
    writestartupfile(parameter_dict)

    MeshF = parameter_dict['meshfn']
    ModF  = parameter_dict['inmodelfn']
    SF    = parameter_dict['startupfn']
    
    return (MeshF,ModF,SF)

def writemeshfile(parameter_dict):

    mesh_positions_vert = parameter_dict['mesh_positions_vert']
    mesh_positions_hor  = parameter_dict['mesh_positions_hor']
    n_nodes_hor         = parameter_dict['n_nodes_hor']
    n_nodes_vert        = parameter_dict['n_nodes_vert']
    
    fh_mesh = file(parameter_dict['meshfn'],'w')
    mesh_outstring =''

    temptext = "MESH FILE FROM MTpy\n"
    mesh_outstring += temptext

    temptext = "%i %i %i %i %i %i\n"%(0,n_nodes_hor,n_nodes_vert,0,0,2)
    mesh_outstring += temptext

    temptext = ""
    for i in range(n_nodes_hor-1):
        temptext += "%.1f "%(mesh_positions_hor[i])
    temptext +="\n"
    mesh_outstring += temptext

    temptext = ""
    for i in range(n_nodes_vert-1):
        temptext += "%.1f "%(mesh_positions_vert[i])
    temptext +="\n"
    mesh_outstring += temptext

    mesh_outstring +="%i\n"%(0)

    for j in range(4*(n_nodes_vert-1)):
        tempstring=''
        tempstring += (n_nodes_hor-1)*"?"
        tempstring += '\n'
        mesh_outstring += tempstring
    

    fh_mesh.write(mesh_outstring)
    fh_mesh.close()



def writemodelfile(parameter_dict):
    "needed : filename,binding_offset,startcolumn, n_layers,layer_thickness,block_width"

    modelblockstrings = parameter_dict['modelblockstrings']
    nfev              = parameter_dict['nfev']
    lo_colnumbers     = parameter_dict['lo_colnumbers']
    boffset           = float(parameter_dict['binding_offset'])
    n_layers          = int(float(parameter_dict['n_layers']))

    
    fh_model = file(parameter_dict['inmodelfn'],'w')
    model_outstring =''

    temptext = "Format:           %s\n"%("OCCAM2MTMOD_1.0")
    model_outstring += temptext
    temptext = "Model Name:       %s\n"%(parameter_dict['modelname'])
    model_outstring += temptext
    temptext = "Description:      %s\n"%("Random Text")
    model_outstring += temptext
    temptext = "Mesh File:        %s\n"%(os.path.basename(parameter_dict['meshfn']))
    model_outstring += temptext
    temptext = "Mesh Type:        %s\n"%("PW2D")
    model_outstring += temptext
    temptext = "Statics File:     %s\n"%("none")
    model_outstring += temptext
    temptext = "Prejudice File:   %s\n"%("none")
    model_outstring += temptext
    temptext = "Binding Offset:   %.1f\n"%(boffset)
    model_outstring += temptext
    temptext = "Num Layers:       %i\n"%(n_layers)
    model_outstring += temptext

    for k in range(n_layers):
        n_meshlayers  = nfev[k]
        n_meshcolumns = lo_colnumbers[k]
        temptext="%i %i\n"%(n_meshlayers, n_meshcolumns)
        model_outstring += temptext

        temptext = modelblockstrings[k]
        model_outstring += temptext
        #model_outstring += "\n"
        

    temptext = "Number Exceptions:%i\n"%(0)
    model_outstring += temptext
    

    fh_model.write(model_outstring)
    fh_model.close()



def writestartupfile(parameter_dict):


    fh_startup = file(parameter_dict['startupfn'],'w')
    startup_outstring =''

    temptext = "Format:           %s\n"%(parameter_dict['itform'])
    startup_outstring += temptext
    temptext = "Description:      %s\n"%(parameter_dict['description'])
    startup_outstring += temptext
    temptext = "Model File:       %s\n"%(os.path.basename(parameter_dict['inmodelfn']))
    startup_outstring += temptext
    temptext = "Data File:        %s\n"%(os.path.basename(parameter_dict['datafile']))
    startup_outstring += temptext
    temptext = "Date/Time:        %s\n"%(parameter_dict['datetime'])
    startup_outstring += temptext
    temptext = "Max Iter:         %i\n"%(int(float(parameter_dict['n_max_iterations'])))
    startup_outstring += temptext
    temptext = "Req Tol:          %.1g\n"%(float(parameter_dict['targetrms']))
    startup_outstring += temptext
    temptext = "IRUF:             %s\n"%(parameter_dict['iruf'])
    startup_outstring += temptext
    temptext = "Debug Level:      %s\n"%(parameter_dict['idebug'])
    startup_outstring += temptext
    temptext = "Iteration:        %i\n"%(int(float(parameter_dict['n_max_iterations'])))
    startup_outstring += temptext
    temptext = "PMU:              %s\n"%(parameter_dict['pmu'])
    startup_outstring += temptext
    temptext = "Rlast:            %s\n"%(parameter_dict['rlast'])
    startup_outstring += temptext
    temptext = "Tlast:            %s\n"%(parameter_dict['tobt'])
    startup_outstring += temptext
    temptext = "IffTol:           %s\n"%(parameter_dict['ifftol'])
    startup_outstring += temptext
    temptext = "No. Parms:        %i\n"%(int(float(parameter_dict['n_parameters'])))
    startup_outstring += temptext
    temptext = ""
    for l in range(int(float(parameter_dict['n_parameters']))):
        temptext += "%.1g  "%(2.0)
    temptext += "\n"
    startup_outstring += temptext
     

    fh_startup.write(startup_outstring)
    fh_startup.close()

def read_datafile(parameter_dict):


    df = parameter_dict['datafile']
    F  = file(df,'r')
    datafile_content = F.readlines()
    F.close()

    #RELYING ON A CONSTANT FORMAT, ACCESSING THE PARTS BY COUNTING OF LINES!!!:
    
    n_sites = int(datafile_content[2].strip().split()[1])
    sitenames = []
    for i in range(n_sites):
        sitenames.append(datafile_content[3+i].strip())

    sitelocations=[]
    for i in range(n_sites):
        idx = 4+n_sites+i
        sitelocations.append(float(datafile_content[idx].strip()))

    n_freqs = int(datafile_content[2*n_sites+4].strip().split()[1])
    freqs=[]
    for i in range(n_freqs):
        idx = 2*n_sites+5+i
        freqs.append(float(datafile_content[idx].strip()))


    n_data = int(datafile_content[2*n_sites+5+n_freqs].strip().split()[2])
    

    parameter_dict['lo_site_names']     = sitenames
    parameter_dict['lo_site_locations'] = sitelocations
    parameter_dict['n_sites']           = n_sites
    parameter_dict['n_datapoints']      = n_data
    parameter_dict['n_freqs']           = n_freqs
    parameter_dict['lo_freqs']          = freqs
    
    

def get_model_setup(parameter_dict):

    ncol0      = int(float(parameter_dict['ncol0']))
    n_layer    = int(float(parameter_dict['n_layers']))
    nfe        = parameter_dict['nfe']
    thickness  = parameter_dict['thickness']
    width      = parameter_dict['width']
    trigger    =  float(parameter_dict['trigger'])
    dlz = parameter_dict['dlz']

    modelblockstrings = []
    lo_colnumbers     = []

    ncol     = ncol0
    np       = 0

    
    for layer_idx in range(n_layer):
        block_idx = 1

        #print layer_idx,len(thickness),len(width),ncol,len(dlz)
    
        while block_idx+2 < ncol-1 :

            #PROBLEM : 'thickness' has only "n_layer'-1 entries!!
            if not dlz[layer_idx] > (trigger*(width[block_idx]+width[block_idx+1])):
                block_idx += 1
                continue

            else:
                width[block_idx] += width[block_idx+1]
                nfe[block_idx]   += nfe[block_idx+1]

                for m in range(block_idx+2,ncol):
                    width[m-1] = width[m]
                    nfe[m-1]   = nfe[m]

                ncol -=1

        lo_colnumbers.append(ncol)

        tempstring = ""
        for j in range(ncol):
            tempstring += "%i "%(nfe[j])
        tempstring += "\n"
        modelblockstrings.append(tempstring)

        np = np + ncol

        #completely unnecessary!!! :
        if layer_idx == 0:
            mcol = ncol
        

    parameter_dict['modelblockstrings'] = modelblockstrings
    parameter_dict['lo_colnumbers']     = lo_colnumbers
    parameter_dict['n_parameters']      = np
    parameter_dict['n_cols_max']        = mcol
    

def blocks_elements_setup(parameter_dict):
    

    lo_sites = parameter_dict['lo_site_locations']
    n_sites  = len(lo_sites)
    maxwidth = float(parameter_dict['max_blockwidth'])

    nbot     = int(float(parameter_dict['n_bottomlayerelements']))
    nside    = int(float(parameter_dict['n_sideblockelements']))

    # j: index for finite elements
    # k: index for regularisation bricks
    # Python style: start with 0 instead of 1

    sitlok      = []
    sides       = []
    width       = []
    dly         = []
    nfe         = []
    thickness   = []
    nfev        = []
    dlz         = []
    bot         = []

    
    j = 0
    sitlok.append(lo_sites[0])

    for idx in range(1,n_sites-1):
        
        spacing           = lo_sites[idx] - lo_sites[idx-1]
        n_localextrasites = int(spacing/maxwidth) + 1

        for idx2 in range(n_localextrasites):
            sitlok.append(lo_sites[idx-1] + (idx2+1.)/float(n_localextrasites)*spacing )
            j += 1

    # nrk: number of total dummy stations
    nrk = j
    print "%i dummy stations defined"%(nrk)

    
    spacing1 = (sitlok[1]-sitlok[0])/2.
    sides.append(3*spacing1)


    for idx in range(1,nside):
        curr_side = 3*sides[idx-1]
        if curr_side > 1000000.:
            curr_side = 1000000.
        sides.append(curr_side)
        
    #-------------------------------------------

    j = 0
    k = 0

    firstblockwidth = 0.
    
    for idx in range(nside-1,-1,-1):
        firstblockwidth += sides[idx]
        dly.append(sides[idx])
        j += 1
        
    width.append(firstblockwidth)
    nfe.append(nside)
    
    dly.append(spacing1)
    dly.append(spacing1)
    j += 2
    nfe.append(2)
    width.append(2*spacing1)

    block_offset = width[1]

    k += 1

    dly.append(spacing1)
    dly.append(spacing1)
    j += 2
    nfe.append(2)
    width.append(2*spacing1)
    
    block_offset += spacing1

    k += 1

    #------------------------
    
    for idx in range(1,nrk-1):
        spacing2 = (sitlok[idx+1]-sitlok[idx])/2.
        dly.append(spacing1)
        dly.append(spacing2)
        j += 2
        nfe.append(2)
        width.append(spacing1+spacing2)
        k += 1
        spacing1 = spacing2

    dly.append(spacing2)
    dly.append(spacing2)

    j += 2
    nfe.append(2)
    width.append(2*spacing2)
    k += 1

    dly.append(spacing2)
    dly.append(spacing2)
    
    j += 2
    nfe.append(2)
    width.append(2*spacing2)
    k += 1

    width[-1] = 0.
    sides[0] = 3*spacing2

    #------------------------------
    
    for idx in range(1,nside):
        curr_side = 3*sides[idx-1]
        if curr_side > 1000000.:
            curr_side = 1000000.
        sides[idx] = curr_side


    lastblockwidth= 0.
    for idx in range(nside):
        j += 1
        lastblockwidth += sides[idx]
        dly.append(sides[idx])

    width[-1] = lastblockwidth

    #---------------------------------

    k+= 1
    nfe.append(nside)

    nodey = j+1
    ncol0 = k

    block_offset = sitlok[0] - block_offset

    #----------------------------------

    layers_per_decade     = float(parameter_dict['n_layersperdecade'])
    first_layer_thickness = float(parameter_dict['firstlayer_thickness'])

    t          = 10.**(1./layers_per_decade)
    t1         = first_layer_thickness
    thickness.append(t1)
    
    d1 = t1
    
    n_layers = int(float(parameter_dict['n_layers']))

    for idx in range(1,n_layers-1):
        d2 = d1*t
        curr_thickness = d2 - d1
        if curr_thickness < t1:
            curr_thickness = t1
        thickness.append(curr_thickness)
        d1 += curr_thickness
    
    
    bot.append(3*thickness[n_layers-2])

    for idx in range(1,nbot):
        bot.append(bot[idx-1]*3)

    #--------------------------------------------------

    k = 0
    
    dlz.append(thickness[0]/2.)
    dlz.append(thickness[0]/2.)
    nfev.append(2)

    k += 2

    dlz.append(thickness[1]/2.)
    dlz.append(thickness[1]/2.)
    nfev.append(2)

    k += 2

    for idx in range(2,n_layers-1):
        k += 1
        nfev.append(1.)
        dlz.append(thickness[idx])

    for idx in range(nbot):
        k += 1
        dlz.append(bot[idx])

    nfev.append(nbot)

    nodez = k+1
    

    parameter_dict['ncol0']             = ncol0
    parameter_dict['nfe']               = nfe
    parameter_dict['nfev']              = nfev
    parameter_dict['thickness']         = thickness
    parameter_dict['width']             = width
    parameter_dict['binding_offset']    = block_offset
    #parameter_dict['y_nodes']           = nodey 
    #parameter_dict['z_nodes']           = nodez
    parameter_dict['dlz']               = dlz
    #parameter_dict['dly']               = dly
    parameter_dict['mesh_positions_vert'] = dlz
    parameter_dict['mesh_positions_hor']  = dly
    parameter_dict['n_nodes_hor']         = nodey
    parameter_dict['n_nodes_vert']        = nodez
    
    
class OccamPointPicker(object):
    """
    This class will help the user interactively pick points to mask and add 
    error bars. 
    
    To mask just a single point right click over the point and a gray point 
    will appear indicating it has been masked
    
    To mask both the apparent resistivity and phase left click over the point.
    Gray points will appear over both the apparent resistivity and phase.  
    Sometimes the points don't exactly matchup, haven't quite worked that bug
    out yet, but not to worry it picks out the correct points
    
    To add error bars to a point click the middle or scroll bar button.  This
    only adds error bars to the point and does not reduce them so start out
    with reasonable errorbars.  You can change the increment that the error
    bars are increased with reserrinc and phaseerrinc.
    
    Inputs:
        axlst = list of the resistivity and phase axis that have been plotted
                as [axrte,axrtm,axpte,axptm]
        
        linelst = list of lines used to plot the responses, not the error bars
        
        errlst = list of the errorcaps and errorbar lines as 
                   [[cap1,cap2,bar],...]
                 
        reserrinc = percent increment to increase the errorbars
        
        phaseerrinc = percent increment to increase the errorbars
    """    
    
    def __init__(self,axlst,linelst,errlst,reserrinc=.05,phaseerrinc=.02,
                 marker='h'):
        #give the class some attributes
        self.axlst=axlst
        self.linelst=linelst
        self.errlst=errlst
        self.data=[]
        self.error=[]
        self.fdict=[]
        self.fndict={}
        #see if just one figure is plotted or multiple figures are plotted
        self.ax=axlst[0][0]
        self.line=linelst[0][0]
        self.cidlst=[]
        for nn in range(len(axlst)):
            self.data.append([])
            self.error.append([])
            self.fdict.append([])
        
            #get data from lines and make a dictionary of frequency points for easy
            #indexing
            for ii,line in enumerate(linelst[nn]):
                self.data[nn].append(line.get_data()[1])
                self.fdict[nn].append(dict([('{0:.5g}'.format(kk),ff) for ff,kk in 
                                        enumerate(line.get_data()[0])]))
                self.fndict['{0}'.format(line.figure.number)]=nn
                
                #set some events
                if ii==0:
                    cid1=line.figure.canvas.mpl_connect('pick_event',self)
                    cid2=line.figure.canvas.mpl_connect('axes_enter_event',
                                                        self.inAxes)
                    cid3=line.figure.canvas.mpl_connect('key_press_event',
                                                        self.on_close)
                    cid4=line.figure.canvas.mpl_connect('figure_enter_event',
                                                        self.inFigure)
                    self.cidlst.append([cid1,cid2,cid3,cid4])
        
            #read in the error in a useful way so that it can be translated to 
            #the data file.  Make the error into an array
            for ee,err in enumerate(errlst[nn]):
                errpath=err[2].get_paths()
                errarr=np.zeros(len(self.fdict[nn][ee].keys()))
                for ff,epath in enumerate(errpath):
                    errv=epath.vertices
                    errarr[ff]=abs(errv[0,1]-self.data[nn][ee][ff])
                self.error[nn].append(errarr)
        
        #set the error bar increment values
        self.reserrinc=reserrinc
        self.phaseerrinc=phaseerrinc
        #set the marker
        self.marker=marker
        #set the figure number
        self.fignum=self.line.figure.number
        #make a list of occam lines to write later
        self.occamlines=[]
    
        
        
    
    def __call__(self,event):
        """
        When the function is called the mouse events will be recorder for 
        picking points to mask or change error bars.
        
        Left mouse button will mask both resistivity and phase point
        
        Right mouse button will mask just the point selected
        
        middle mouse button will increase the error bars
        
        q will close the figure.
        """
        self.event=event
        #make a new point that is an PickEvent type
        npoint=event.artist
        #if the right button is clicked mask the point
        if event.mouseevent.button==3:
            #get the point that was clicked on
            ii=event.ind
            xd=npoint.get_xdata()[ii]
            yd=npoint.get_ydata()[ii]
            
            #set the x index from the frequency dictionary
            ll=self.fdict[self.fignum][self.jj]['{0:.5g}'.format(xd[0])]
            
            #change the data to be a zero
            self.data[self.fignum][self.jj][ll]=0
            
            #reset the point to be a gray x
            self.ax.plot(xd,yd,ls='None',color=(.7,.7,.7),marker=self.marker,
                         ms=4)
        
        #if the left button is clicked change both resistivity and phase points
        elif event.mouseevent.button==1:
            #get the point that was clicked on
            ii=event.ind
            xd=npoint.get_xdata()[ii]
            yd=npoint.get_ydata()[ii]
            
            #set the x index from the frequency dictionary
            ll=self.fdict[self.fignum][self.jj]['{0:.5g}'.format(xd[0])]
            
            #set the data point to zero
            self.data[self.fignum][self.jj][ll]=0
            
            #reset the point to be a gray x
            self.ax.plot(xd,yd,ls='None',color=(.7,.7,.7),marker=self.marker,
                         ms=4)
            
            #check to make sure there is a corresponding res/phase point
            try:
                #get the corresponding y-value 
                yd2=self.data[self.fignum][self.kk][ll]
                
                #set that data point to 0 as well
                self.data[self.fignum][self.kk][ll]=0
                
                #make that data point a gray x
                self.axlst[self.fignum][self.kk].plot(xd,yd2,ls='None',
                                        color=(.7,.7,.7),marker=self.marker,
                                        ms=4)
            except KeyError:
                print 'Axis does not contain res/phase point'
                
        #if click the scroll button or middle button change increase the 
        #errorbars by the given amount
        elif event.mouseevent.button==2:
            ii=event.ind
            xd=npoint.get_xdata()[ii]
            yd=npoint.get_ydata()[ii]
            
            #get x index
            ll=self.fdict[self.fignum][self.jj]['{0:.5g}'.format(xd[0])]
            
            #make error bar array
            eb=self.errlst[self.fignum][self.jj][2].get_paths()[ll].vertices
            
            #make ecap array
            ecapl=self.errlst[self.fignum][self.jj][0].get_data()[1][ll]
            ecapu=self.errlst[self.fignum][self.jj][1].get_data()[1][ll]
            
            #change apparent resistivity error
            if self.jj==0 or self.jj==1:
                nebu=eb[0,1]-self.reserrinc*eb[0,1]
                nebl=eb[1,1]+self.reserrinc*eb[1,1]
                ecapl=ecapl-self.reserrinc*ecapl
                ecapu=ecapu+self.reserrinc*ecapu
                
            #change phase error
            elif self.jj==2 or self.jj==3:
                nebu=eb[0,1]-eb[0,1]*self.phaseerrinc
                nebl=eb[1,1]+eb[1,1]*self.phaseerrinc
                ecapl=ecapl-ecapl*self.phaseerrinc
                ecapu=ecapu+ecapu*self.phaseerrinc
                
            #put the new error into the error array    
            self.error[self.fignum][self.jj][ll]=abs(nebu-\
                                        self.data[self.fignum][self.jj][ll])
            
            #set the new error bar values
            eb[0,1]=nebu
            eb[1,1]=nebl
            
            #reset the error bars and caps
            ncapl=self.errlst[self.fignum][self.jj][0].get_data()
            ncapu=self.errlst[self.fignum][self.jj][1].get_data()
            ncapl[1][ll]=ecapl
            ncapu[1][ll]=ecapu
            
            #set the values 
            self.errlst[self.fignum][self.jj][0].set_data(ncapl)
            self.errlst[self.fignum][self.jj][1].set_data(ncapu)
            self.errlst[self.fignum][self.jj][2].get_paths()[ll].vertices=eb
            
        #redraw the canvas
        self.ax.figure.canvas.draw()

    #get the axis number that the mouse is in and change to that axis
    def inAxes(self,event):
        self.event2=event
        self.ax=event.inaxes
        for jj,axj in enumerate(self.axlst):
            for ll,axl in enumerate(axj):
                if self.ax==axl:
                    self.jj=ll
                
        #set complimentary resistivity and phase plots together
        if self.jj==0:
            self.kk=2
        if self.jj==1:
            self.kk=3
        if self.jj==2:
            self.kk=0
        if self.jj==3:
            self.kk=1
        
    #get the figure number that the mouse is in
    def inFigure(self,event):
        self.event3=event
        self.fignum=self.fndict['{0}'.format(event.canvas.figure.number)]
        self.line=self.linelst[self.fignum][0]
    
    #type the q key to quit the figure and disconnect event handling            
    def on_close(self,event):
        self.event3=event
        if self.event3.key=='q':
            for cid in self.cidlst[self.fignum]:
               event.canvas.mpl_disconnect(cid)
            plt.close(event.canvas.figure)
            print 'closed'     
            
class Occam2DData:
    def __init__(self,datafn=None):
        self.datafn=datafn
        
    def make2DdataFile(self,edipath,mmode='both',savepath=None,stationlst=None,
                       title=None,thetar=0,resxyerr=10,resyxerr=10,
                       phasexyerr=5,phaseyxerr=5,ss=3*' ',fmt='%2.6f',
                       freqstep=1,plotyn='y',lineori='ew',tippererr=None,
                       ftol=.05):
        """
        make2DdataFile will make a data file for occam2D.  
        
        Input:
            edipath = path to edifiles
            mmode = modes to invert for.  Can be: 
                    'both' -> will model both TE and TM modes
                    'TM'   -> will model just TM mode
                    'TE'   -> will model just TE mode
            savepath = path to save the data file to, this can include the name of
                       the data file, if not the file will be named:
                           savepath\Data.dat or edipath\Data.dat if savepath=None
            stationlst = list of stations to put in the data file, doesn't need to
                         be in order, the relative distance will be calculated
                         internally.  If stationlst=None, it will be assumed all the
                         files in edipath will be input into the data file
            title = title input into the data file
            thetar = rotation angle (deg) of the edifiles if you want to align the
                     components with the profile.  Angle is on the unit circle with 
                     an orientation that north is 0 degree, east -90.
            resxyerr = percent error in the res_xy component (TE), 
                      can be entered as 'data' where the errors from the data are
                      used.  
            resyxerr = percent error in the res_yx component (TM), 
                      can be entered as 'data' where the errors from the data are
                      used.  
            phasexyerr = percent error in the phase_xy component (TE), 
                      can be entered as 'data' where the errors from the data are
                      used.  
            phaseyxerr = percent error in the phase_yx component (TM), 
                      can be entered as 'data' where the errors from the data are
                      used.  
            ss = is the spacing parameter for the data file
            fmt = format of the numbers for the data file, see string formats for 
                  a full description
            freqstep = take frequencies at this step, so if you want to take every
                       third frequency enter 3.  
                       Can input as a list of specific frequencies.  Note that the
                       frequencies must match the frequencies in the EDI files,
                       otherwise they will not be input.  
            plotyn = y or n to plot the stations on the profile line.
            lineori = predominant line orientation with respect to geographic north
                     ew for east-west line-> will orientate so first station is 
                                             farthest to the west
                     ns for north-south line-> will orientate so first station is 
                                             farthest to the south
            tippererr = error for tipper in percent.  If this value is entered than
                        the tipper will be included in the inversion, if the value
                        is None than the tipper will not be included.
                  
        Output:
            datfilename = full path of data file
                     
        """
        
        if abs(thetar)>2*np.pi:
            thetar=thetar*(np.pi/180)
        #create rotation matrix
        rotmatrix=np.array([[np.cos(thetar), np.sin(thetar)],
                             [-np.sin(thetar), np.cos(thetar)]])
        
        #-----------------------Station Locations-----------------------------------    
        #create a list to put all the station dictionaries into
        surveylst=[]
        eastlst=[]
        northlst=[]
        pstationlst=[]
        freqlst=[]
        
        if stationlst==None:
            stationlst=[edifile[:-4] 
                for edifile in os.listdir(edipath) if edifile.find('.edi')]
        
        for kk,station in enumerate(stationlst):
            #search for filenames in the given directory and match to station name
            for filename in os.listdir(edipath):
                if fnmatch.fnmatch(filename,station+'*.edi'):
                    print 'Found station edifile: ', filename
                    surveydict={} #create a dictionary for the station data and info
                    edifile=os.path.join(edipath,filename) #create filename path
                    z1=Z.Z(edifile)
                    freq=z1.frequency                
                    #check to see if the frequency is in descending order
                    if freq[0]<freq[-1]:
                        freq=freq[::-1]
                        z=z1.z[::-1,:,:]
                        zvar=z1.zvar[::-1,:,:]
                        tip=z1.tipper[::-1,:,:]
                        tipvar=z1.tippervar[::-1,:,:]
                        
                        print 'Flipped to descending frequency for station '+station
                    else:
                        z=z1.z
                        zvar=z1.zvar
                        tip=z1.tipper
                        tipvar=z1.tippervar
                    #rotate matrices if angle is greater than 0
                    if thetar!=0:
                        for rr in range(len(z)):
                            z[rr,:,:]=np.dot(rotmatrix,np.dot(z[rr],rotmatrix.T))
                            zvar[rr,:,:]=np.dot(rotmatrix,np.dot(zvar[rr],
                                                                 rotmatrix.T))
                    else:
                        pass
                            
                    #get eastings and northings so everything is in meters
                    zone,east,north=utm2ll.LLtoUTM(23,z1.lat,z1.lon)
                    #put things into a dictionary to sort out order of stations
                    surveydict['station']=station
                    surveydict['east']=east
                    surveydict['north']=north
                    surveydict['zone']=zone
                    surveydict['z']=z
                    surveydict['zvar']=zvar
                    surveydict['freq']=freq
                    surveydict['tipper']=tip
                    surveydict['tippervar']=tipvar
                    surveydict['lat']=z1.lat
                    surveydict['lon']=z1.lon
                    freqlst.append(freq)
                    eastlst.append(east)
                    northlst.append(north)
                    pstationlst.append(station)
                    surveylst.append(surveydict)
        
        #-----------------------------------------------------------------            
        #project stations onto a best fitting line taking into account the 
        #strike direction to get relative MT distance correct
        #-----------------------------------------------------------------
        
        #get bestfitting line
        p=sp.polyfit(eastlst,northlst,1)
        
        #the angle of the line is now the angle of the best fitting line added
        #to the geoelectric strike direction, which gives the relative distance
        #along the strike direction.
        theta=np.arctan(p[0])
        print 'Profile Line Angle is: {0:.4g} (E=0,N=90)'.format(theta*180/np.pi)
        
        #plot stations on profile line
        if plotyn=='y':
            lfig=plt.figure(4,dpi=200)
            lax=lfig.add_subplot(1,1,1,aspect='equal')
            lax.plot(eastlst,sp.polyval(p,eastlst),'-b',lw=2)
            lax.set_title('Projected Stations')
        for ii in range(len(surveylst)):
            if surveylst[ii]['zone']!=surveylst[0]['zone']:
                print surveylst[ii]['station']
            d=(northlst[ii]-sp.polyval(p,eastlst[ii]))*np.cos(theta)
            x0=eastlst[ii]+d*np.sin(theta)
            y0=northlst[ii]-d*np.cos(theta)
            surveylst[ii]['east']=x0
            surveylst[ii]['north']=y0
            
            
            #need to figure out a way to account for zone changes
            
            if lineori=='ew': 
                if surveylst[0]['east']<surveylst[ii]['east']:
                    surveylst[ii]['offset']=np.sqrt((surveylst[0]['east']-
                                                    surveylst[ii]['east'])**2+
                                                    (surveylst[0]['north']-
                                                    surveylst[ii]['north'])**2)
                elif surveylst[0]['east']>surveylst[ii]['east']:
                    surveylst[ii]['offset']=-1*np.sqrt((surveylst[0]['east']-
                                                    surveylst[ii]['east'])**2+
                                                    (surveylst[0]['north']-
                                                    surveylst[ii]['north'])**2)
                else:
                    surveylst[ii]['offset']=0
            elif lineori=='ns': 
                if surveylst[0]['north']<surveylst[ii]['north']:
                    surveylst[ii]['offset']=np.sqrt((surveylst[0]['east']-
                                                    surveylst[ii]['east'])**2+
                                                    (surveylst[0]['north']-
                                                    surveylst[ii]['north'])**2)
                elif surveylst[0]['north']>surveylst[ii]['north']:
                    surveylst[ii]['offset']=-1*np.sqrt((surveylst[0]['east']-
                                                    surveylst[ii]['east'])**2+
                                                    (surveylst[0]['north']-
                                                    surveylst[ii]['north'])**2)
                else:
                    surveylst[ii]['offset']=0
                    
            if plotyn=='y':
#                ds=surveylst[ii]['offset']*np.sin(thetar)*(1-np.tan(thetar)**2)
#                lax.plot(x0+ds*np.cos(thetar),y0+ds*np.sin(thetar),'v',
#                         color='k',ms=8,mew=3)
                lax.plot(x0,y0,'v',color='k',ms=8,mew=3)
                lax.text(x0,y0+.0005,pstationlst[ii],horizontalalignment='center',
                     verticalalignment='baseline',fontdict={'size':12,
                                                            'weight':'bold'})
        
        #sort by ascending order of distance from first station
        surveylst=sorted(surveylst,key=itemgetter('offset'))
        
        #number of stations read    
        nstat=len(surveylst)    
        
        #--------------------------Match Frequencies---------------------------
        #a dictionary is created with the frequency as the key and the value is
        #the frequency number in the list. Each edi file is iterated over 
        #extracting only the matched frequencies.  This makes it necessary to 
        #have the same frequency content in each edifile.  If the frequencies
        #do not match then you can specify a tolerance to look around for 
        #each frequency.
        
        #make a list to iterate over frequencies
        if type(freqstep) is list or type(freqstep) is not int:
            if type(freqstep[0]) is int:
                #find the median frequency list
                maxflen=max([len(ff) for ff in freqlst])
                farray=np.zeros((nstat,maxflen))
                for ii in range(nstat):
                    farray[ii,0:len(freqlst[ii])]=freqlst[ii]
            
                mfreq=np.median(farray,axis=0)
                print len(mfreq),len(freqstep)
                fdict=dict([('%.6g' % mfreq[ff],ii) 
                                for ii,ff in enumerate(freqstep,1) if mfreq[ff]!=0])
            else:
                fdict=dict([('%.6g' % ff,ii) for ii,ff in enumerate(freqstep,1)])
        else:
            #find the median frequency list
            maxflen=max([len(ff) for ff in freqlst])
            farray=np.zeros((nstat,maxflen))
            for ii in range(nstat):
                farray[ii,0:len(freqlst[ii])]=freqlst[ii]
            
            mfreq=np.median(farray,axis=0)
        
            #make a dictionary of values        
            fdict=dict([('%.6g' % ff,ii) for ii,ff in 
                        enumerate(mfreq[range(0,maxflen,freqstep)],1) if ff!=0])
    
        #print the frequencies to look for to make sure its what the user wants
        #make a list of keys that is sorted in descending order
        klst=[float(dd) for dd in fdict.keys()]
        klst.sort(reverse=True)
        klst=['%.6g' % dd for dd in klst]    
        
        print 'Frequencies to look for are: (# freq(Hz) Period(s)) '
        for key in klst:
            print fdict[key],key, 1./float(key)
        
        #make lists of parameters to write to file    
        reslst=[]
        offsetlst=[]
        stationlstsort=[]
        for kk in range(nstat):
            z=surveylst[kk]['z']
            zvar=surveylst[kk]['zvar']
            freq=surveylst[kk]['freq']
            offsetlst.append(surveylst[kk]['offset'])  
            stationlstsort.append(surveylst[kk]['station'])
            tip=surveylst[kk]['tipper']
            tipvar=surveylst[kk]['tippervar']
            #loop over frequencies to pick out the ones desired
            for jj,ff in enumerate(freq):
                #jj is the index of edi file frequency list, this index 
                #corresponds to the impedance tensor component index
                #ff is the frequency from the edi file frequency list
                try:
                    #nn is the frequency number out of extracted frequency list
                    nn=fdict['%.6g' % ff]
                    
                    #calculate apparent resistivity 
                    wt=.2/(ff)
                    resxy=wt*abs(z[jj,0,1])**2
                    resyx=wt*abs(z[jj,1,0])**2
            
                    #calculate the phase putting the yx in the 1st quadrant        
                    phasexy=np.arctan2(z[jj,0,1].imag,z[jj,0,1].real)*(180/np.pi)
                    phaseyx=np.arctan2(z[jj,1,0].imag,z[jj,1,0].real)*(180/np.pi)+\
                            180
                    #put phases in correct quadrant if should be negative
                    if phaseyx>180:
                        phaseyx=phaseyx-360
                        print 'Found Negative Phase',surveylst[kk]['station'],ff    
                    
                    #calculate errors
                    #res_xy (TE)
                    if resxyerr=='data':
                        dresxyerr=wt*(abs(z[jj,0,1])+zvar[jj,0,1])**2-resxy
                        lresxyerr=(dresxyerr/resxy)/np.log(10)
                    
                    else:
                        lresxyerr=(resxyerr/100.)/np.log(10)
                    
                    #Res_yx(TM)
                    if resyxerr=='data':
                        dresyxerr=wt*(abs(z[jj,1,0])+zvar[jj,1,0])**2-resyx
                        lresyxerr=(dresyxerr/resyx)/np.log(10)
                    else:
                        lresyxerr=(resyxerr/100.)/np.log(10)
                    
                    #phase_xy(TE)
                    if phasexyerr=='data':
                        dphasexyerr=np.arcsin(zvar[jj,0,1]/abs(z[jj,0,1]))*\
                                    (180/np.pi)
                    else:
                        dphasexyerr=(phasexyerr/100.)*57/2.
                        
                    #phase_yx (TM)
                    if phaseyxerr=='data':
                        dphaseyxerr=np.arcsin(zvar[jj,1,0]/abs(z[jj,1,0]))*\
                                    (180/np.pi)
                    else:
                        dphaseyxerr=(phaseyxerr/100.)*57/2.
                    
                    #calculate log10 of resistivity as prescribed by OCCAM
                    lresyx=np.log10(resyx)
                    lresxy=np.log10(resxy)
                    
                    #if include the tipper
                    if tippererr!=None:
                        if tip[jj,0].real==0.0 or tip[jj,1]==0.0:
                            tipyn='n'
                        else:
                            #calculate the projection angle for real and imaginary
                            tipphir=np.arctan(tip[jj,0].real/tip[jj,1].real)-\
                                    theta
                            tipphii=np.arctan(tip[jj,0].imag/tip[jj,1].imag)-\
                                    theta
                            
                            #project the tipper onto the profile line
                            projtipr=np.sqrt(tip[jj,0].real**2+tip[jj,1].real**2)*\
                                      np.cos(tipphir)
                            projtipi=np.sqrt(tip[jj,0].imag**2+tip[jj,1].imag**2)*\
                                      np.cos(tipphii)
                                      
                            #error of tipper is a decimal percentage
                            projtiperr=tippererr/100.
                            
                            tipyn='y'
                            
                        
                    #make a list of lines to write to the data file
                    if mmode=='both':
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                        fmt % lresxy +ss+fmt % lresxyerr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                        fmt % phasexy +ss+fmt % dphasexyerr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                        fmt % lresyx+ss+fmt % lresyxerr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                        fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                        if tippererr!=None and tipyn=='y':
                            reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                        fmt % projtipr +ss+fmt % projtiperr+'\n')
                            reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                        fmt % projtipi +ss+fmt % projtiperr+'\n')
                    elif mmode=='TM':
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                        fmt % lresyx +ss+fmt % lresyxerr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                        fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                        if tippererr!=None and tipyn=='y':
                            reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                        fmt % projtipr +ss+fmt % projtiperr+'\n')
                            reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                        fmt % projtipi +ss+fmt % projtiperr+'\n')
                    elif mmode=='TE':
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                        fmt % lresxy+ss+fmt % lresxyerr+'\n')
                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                        fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                        if tippererr!=None and tipyn=='y':
                            reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                        fmt % projtipr +ss+fmt % projtiperr+'\n')
                            reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                        fmt % projtipi +ss+fmt % projtiperr+'\n')
                    else:
                        raise NameError('mmode' +mmode+' not defined')
                except KeyError:
                    #search around the frequency given by ftol
                    try:
                        for key in fdict.keys():
                            if ff>float(key)*(1-ftol) and ff<float(key)*(1+ftol):
                                nn=fdict[key]                           
                                wt=.2/(ff)
                                resxy=wt*abs(z[jj,0,1])**2
                                resyx=wt*abs(z[jj,1,0])**2
                        
                                #calculate the phase putting the yx in the 1st quadrant        
                                phasexy=np.arctan2(z[jj,0,1].imag,z[jj,0,1].real)*\
                                        (180/np.pi)
                                phaseyx=np.arctan2(z[jj,1,0].imag,z[jj,1,0].real)*\
                                        (180/np.pi)+180
                                #put phases in correct quadrant if should be negative
                                if phaseyx>180:
                                    phaseyx=phaseyx-360
                                    print 'Found Negative Phase',surveylst[kk]['station'],ff    
                                
                                #calculate errors
                                #res_xy (TE)
                                if resxyerr=='data':
                                    dresxyerr=wt*(abs(z[jj,0,1])+zvar[jj,0,1])**2-resxy
                                    lresxyerr=(dresxyerr/resxy)/np.log(10)
                                
                                else:
                                    lresxyerr=(resxyerr/100.)/np.log(10)
                                
                                #Res_yx(TM)
                                if resyxerr=='data':
                                    dresyxerr=wt*(abs(z[jj,1,0])+zvar[jj,1,0])**2-resyx
                                    lresyxerr=(dresyxerr/resyx)/np.log(10)
                                else:
                                    lresyxerr=(resyxerr/100.)/np.log(10)
                                
                                #phase_xy(TE)
                                if phasexyerr=='data':
                                    dphasexyerr=np.arcsin(zvar[jj,0,1]/abs(z[jj,0,1]))*\
                                                (180/np.pi)
                                else:
                                    dphasexyerr=(phasexyerr/100.)*57/2.
                                    
                                #phase_yx (TM)
                                if phaseyxerr=='data':
                                    dphaseyxerr=np.arcsin(zvar[jj,1,0]/abs(z[jj,1,0]))*\
                                                (180/np.pi)
                                else:
                                    dphaseyxerr=(phaseyxerr/100.)*57/2.
                                
                                #calculate log10 of resistivity as prescribed by OCCAM
                                lresyx=np.log10(resyx)
                                lresxy=np.log10(resxy)
                                
                                #if include the tipper
                                if tippererr!=None:
                                    if tip[jj,0].real==0.0 or tip[jj,1]==0.0:
                                        tipyn='n'
                                    else:
                                        #calculate the projection angle for real and imaginary
                                        tipphir=np.arctan(tip[jj,0].real/tip[jj,1].real)-theta
                                        tipphii=np.arctan(tip[jj,0].imag/tip[jj,1].imag)-theta
                                        
                                        #project the tipper onto the profile line
                                        projtipr=np.sqrt(tip[jj,0].real**2+tip[jj,1].real**2)*\
                                                  np.cos(tipphir)
                                        projtipi=np.sqrt(tip[jj,0].imag**2+tip[jj,1].imag**2)*\
                                                  np.cos(tipphii)
                                                  
                                        #error of tipper is a decimal percentage
                                        projtiperr=tippererr/100.
                                        
                                        tipyn='y'
                                        
                                    
                                #make a list of lines to write to the data file
                                if mmode=='both':
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                                    fmt % lresxy +ss+fmt % lresxyerr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                                    fmt % phasexy +ss+fmt % dphasexyerr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                                    fmt % lresyx+ss+fmt % lresyxerr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                                    fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                                    if tippererr!=None and tipyn=='y':
                                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                                    fmt % projtipr +ss+fmt % projtiperr+'\n')
                                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                                    fmt % projtipi +ss+fmt % projtiperr+'\n')
                                elif mmode=='TM':
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'5'+ss+
                                                    fmt % lresyx +ss+fmt % lresyxerr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'6'+ss+
                                                    fmt % phaseyx +ss+fmt % dphaseyxerr+'\n')
                                    if tippererr!=None and tipyn=='y':
                                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                                    fmt % projtipr +ss+fmt % projtiperr+'\n')
                                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                                    fmt % projtipi +ss+fmt % projtiperr+'\n')
                                elif mmode=='TE':
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'1'+ss+
                                                    fmt % lresxy+ss+fmt % lresxyerr+'\n')
                                    reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'2'+ss+
                                                    fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                                    if tippererr!=None and tipyn=='y':
                                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'3'+ss+
                                                    fmt % projtipr +ss+fmt % projtiperr+'\n')
                                        reslst.append(ss+str(kk+1)+ss+str(nn)+ss+'4'+ss+
                                                    fmt % projtipi +ss+fmt % projtiperr+'\n')
                                else:
                                    raise NameError('mmode' +mmode+' not defined')    
                            
                                break                         
                            else:
                                pass
            #                           print 'Did not find frequency {0} for station {1}'.format(ff,surveylst[kk]['station'])
                                #calculate resistivity 
                                   
                    except KeyError:
                        pass
        
        #===========================================================================
        #                             write dat file
        #===========================================================================
        if savepath!=None:
            if os.path.basename(savepath).find('.')>0:
                self.datafn=savepath
            else:
                if not os.path.exists(savepath):
                    os.mkdir(savepath)
                self.datafn=os.path.join(savepath,'Data.dat')
        else:
            self.datafn=os.path.join(edipath,'Data.dat')
            
        if title==None:
            title='Occam Inversion'
            
        datfid=open(self.datafn,'w')
        datfid.write('FORMAT:'+' '*11+'OCCAM2MTDATA_1.0'+'\n')
        datfid.write('TITLE:'+' '*12+'{0:.4g}--'.format(theta*180/np.pi)+' '+\
                      title+'\n')
        
        #write station sites
        datfid.write('SITES:'+' '*12+str(nstat)+'\n')
        for station in stationlstsort:
            datfid.write(ss+station+'\n')
        
        #write offsets
        datfid.write('OFFSETS (M):'+'\n')
        for offset in offsetlst:
            datfid.write(ss+fmt % offset+'\n')
        
        #write frequencies
        #writefreq=[freq[ff] for ff in range(0,len(freq),freqstep)]
        datfid.write('FREQUENCIES:'+' '*8+str(len(fdict))+'\n')
        for fkey in klst:
            datfid.write(ss+fmt % float(fkey) +'\n')
        
        #write data block
        datfid.write('DATA BLOCKS:'+' '*10+str(len(reslst))+'\n')
        datfid.write('SITE'+ss+'FREQ'+ss+'TYPE'+ss+'DATUM'+ss+'ERROR'+'\n')
        for ll,datline in enumerate(reslst):
            if datline.find('#IND')>=0:
                print 'Found #IND on line ',ll
                ndline=datline.replace('#IND','00')
                print 'Replaced with 00'
                datfid.write(ndline)
            else:
                datfid.write(datline)
        datfid.close()
        
        print 'Wrote Occam2D data file to: ',self.datafn
        
    def read2DdataFile(self):
        """
            read2DdataFile will read in data from a 2D occam data file.  
            Only supports the first 6 data types of occam2D
        
        Input: 
            datafn = full path to data file
        
        Output:
            rplst = list of dictionaries for each station with keywords:
                'station' = station name
                'offset' = relative offset,
                'resxy' = TE resistivity and error as row 0 and 1 ressectively,
                'resyx'= TM resistivity and error as row 0 and 1 respectively,
                'phasexy'= TE phase and error as row 0 and 1 respectively,
                'phaseyx'= Tm phase and error as row 0 and 1 respectively,
                'realtip'= Real Tipper and error as row 0 and 1 respectively,
                'imagtip'= Imaginary Tipper and error as row 0 and 1 respectively
                
                Note: that the resistivity will be in log10 space.  Also, there are
                2 extra rows in the data arrays, this is to put the response from
                the inversion. 
            
            stationlst = list of stations in order from one side of the profile
                         to the other.
            freq = list of frequencies used in the inversion
            title = title, could be useful for plotting.
        """
        
        dfid=open(self.datafn,'r')
        
        dlines=dfid.readlines()
        #get format of input data
        self.occamfmt=dlines[0].strip().split(':')[1].strip()
        
        #get title
        self.titlestr=dlines[1].strip().split(':')[1].strip()
    
        if self.titlestr.find('--')>0:
            tstr=self.titlestr.split('--')
            self.theta_profile=float(tstr[0])
            self.title=tstr[1]
        else:
            self.title=self.titlestr
            self.theta_profile=0
            print 'Need to figure out angle of profile line'
        #get number of sits
        nsites=int(dlines[2].strip().split(':')[1].strip())
        
        #get station names
        self.stationlst=[dlines[ii].strip() for ii in range(3,nsites+3)]
        
        #get offsets in meters
        offsets=[float(dlines[ii].strip()) for ii in range(4+nsites,4+2*nsites)]
        
        #get number of frequencies
        nfreq=int(dlines[4+2*nsites].strip().split(':')[1].strip())
    
        #get frequencies
        self.freq=np.array([float(dlines[ii].strip()) 
                                for ii in range(5+2*nsites,5+2*nsites+nfreq)])
        
        #get periods
        self.period=1./self.freq
                                                          
    
        #-----------get data-------------------
        #set zero array size the first row will be the data and second the error
        asize=(4,nfreq)
        #make a list of dictionaries for each station.
        self.rplst=[{'station':station,'offset':offsets[ii],
                'resxy':np.zeros(asize),
                'resyx':np.zeros(asize),
                'phasexy':np.zeros(asize),
                'phaseyx':np.zeros(asize),
                'realtip':np.zeros(asize),
                'imagtip':np.zeros(asize),
                } for ii,station in enumerate(self.stationlst)]
        for line in dlines[7+2*nsites+nfreq:]:
            ls=line.split()
            #station index
            ss=int(float(ls[0]))-1
            #component key
            comp=str(int(float(ls[2])))
            #frequency index        
            ff=int(float(ls[1]))-1
            #print ls,ss,comp,ff
            #put into array
            #input data
            self.rplst[ss][occamdict[comp]][0,ff]=float(ls[3]) 
            #error       
            self.rplst[ss][occamdict[comp]][1,ff]=float(ls[4])
            
    def rewrite2DdataFile(self,edipath=None,thetar=0,resxyerr='prev',
                          resyxerr='prev',phasexyerr='prev',phaseyxerr='prev',
                          tippererr=None,mmode='both',flst=None,
                          removestation=None):
        """
        rewrite2DDataFile will rewrite an existing data file so you can redefine 
        some of the parameters, such as rotation angle, or errors for the different
        components or only invert for one mode or add one or add tipper or remove
        tipper.
        
        Inputs:
            datafn = full path to data file to rewrite
            
            rotz = rotation angle with positive clockwise
            
            resxyerr = error for TE mode resistivity (percent) or 'data' for data 
                        or prev to take errors from data file.
            
            resyxerr = error for TM mode resistivity (percent) or 'data' for data
                        or prev to take errors from data file.
                        
            phasexyerr = error for TE mode phase (percent) or 'data' for data
                        or prev to take errors from data file.
                        
            phaseyxerr = error for TM mode phase (percent) or 'data' for data
                        or prev to take errors from data file.
                        
            tippererr = error for tipper (percent) input only if you want to invert
                        for the tipper or 'data' for data errors
                        or prev to take errors from data file.
                        
            mmodes = 'both' for both TE and TM
                     'TE' for TE
                     'TM' for TM
                     
            flst = frequency list in Hz to rewrite, needs to be similar to the 
                    datafile, cannot add frequencies
                    
            removestation = list of stations to remove if desired
        """
        ss=3*' '
        fmt='%2.6f'
        
        #load the data for the data file    
        self.read2DdataFile()
        #copy the information into local lists in case you want to keep the 
        #original data
        rplst=list(self.rplst)
        stationlst=list(self.stationlst)
        #make a dictionary of rplst for easier extraction of data
        rpdict=dict([(station,rplst[ii]) for ii,station in 
                                                    enumerate(stationlst)])
    
        #remove stations from rplst and stationlst if desired
        if removestation!=None:
            #if removestation is not a list make it one
            if type(removestation) is not list:
                removestation=[removestation]
            
            #remove station from station list           
            for rstation in removestation:        
                try:
                    stationlst.remove(rstation)
                except ValueError:
                    print 'Did not find '+rstation
        
        #if flst is not the same as freq make freq=flst
        if flst!=None:
            freq=flst
        else:
            freq=self.freq
        
        
        #if the rotation angle is not 0 than need to read the original data in
        if thetar!=0:
            if edipath==None:
                raise IOError('Need to input the edipath to original edifiles to'+
                               ' get rotations correct')
            
            #get list of edifiles already in data file
            edilst=[os.path.join(edipath,edi) for stat in stationlst 
                    for edi in os.listdir(edipath) if edi[0:len(stat)]==stat]
            reslst=[]
            for kk,edifn in enumerate(edilst,1):
                imp1=Z.Z(edifn)
                rp=imp1.getResPhase(thetar=thetar)
                imptip=imp1.getTipper()
                tip=imptip.tipper
                station=stationlst[kk-1]
                fdict=dict([('{0:.6g}'.format(fr),ii) for ii,fr in 
                                                    enumerate(imp1.frequency)])
                #loop over frequencies to pick out the ones desired
                for jj,ff in enumerate(freq,1):
                    #jj is the index of edi file frequency list, this index corresponds
                    #to the impedance tensor component index
                    #ff is the frequency from the edi file frequency list
                    try:
                        #nn is the frequency number out of extracted frequency list
                        nn=fdict['%.6g' % ff]
                        
                        #calculate resistivity
                        resxy=rp.resxy[nn]
                        resyx=rp.resyx[nn]
                
                        #calculate the phase putting the yx in the 1st quadrant
                        phasexy=rp.phasexy[nn]
                        phaseyx=rp.phaseyx[nn]+180
                        #put phases in correct quadrant if should be negative
                        if phaseyx>180:
                            phaseyx=phaseyx-360
                            print 'Found Negative Phase at',imp1.station,kk,ff    
                        
                        #calculate errors
                        #res_xy (TE)
                        if resxyerr=='data':
                            lresxyerr=(rp.resxyerr[nn]/resxy)/np.log(10)
                        #take errors from data file
                        elif resxyerr=='prev':
                            lresxyerr=rpdict[station]['resxy'][1,jj-1]
                        else:
                            lresxyerr=(resxyerr/100.)/np.log(10)
                        
                        #Res_yx(TM)
                        if resyxerr=='data':
                            lresxyerr=rpdict[station]['resyx'][1,jj-1]
                        #take errors from data file
                        elif resyxerr=='prev':
                            lresyxerr=rpdict[station]['resyx'][1,jj-1]
                        else:
                            lresyxerr=(resyxerr/100.)/np.log(10)
                        
                        #phase_xy(TE)
                        if phasexyerr=='data':
                            dphasexyerr=rp.phasexyerr[nn]
                            #take errors from data file
                        elif phasexyerr=='prev':
                            dphasexyerr=rpdict[station]['phasexy'][1,jj-1]
                        else:
                            dphasexyerr=(phasexyerr/100.)*57/2.
                            
                        #phase_yx (TM)
                        if phaseyxerr=='data':
                            dphaseyxerr=rp.phaseyxerr[nn]
                        elif phaseyxerr=='prev':
                            dphaseyxerr=rpdict[station]['phaseyx'][1,jj-1]
                        else:
                            dphaseyxerr=(phaseyxerr/100.)*57/2.
                        
                        #calculate log10 of resistivity as prescribed by OCCAM
                        lresyx=np.log10(resyx)
                        lresxy=np.log10(resxy)
                        
                        #if include the tipper
                        if tippererr!=None:
                            if tip[nn,0]==0.0 or tip[nn,1]==0.0:
                                tipyn='n'
                            else:
                                #calculate the projection angle for real and imaginary
                                tipphir=np.arctan(tip[nn,0].real/tip[nn,1].real)-\
                                        self.theta_profile
                                tipphii=np.arctan(tip[nn,0].imag/tip[nn,1].imag)-\
                                        self.theta_profile
                                
                                #project the tipper onto the profile line
                                projtipr=np.sqrt(tip[nn,0].real**2+tip[nn,1].real**2)*\
                                          np.cos(tipphir)
                                projtipi=np.sqrt(tip[nn,0].imag**2+tip[nn,1].imag**2)*\
                                          np.cos(tipphii)
                                          
                                #error of tipper is a decimal percentage
                                projtiperr=tippererr/100.
                                
                                tipyn='y'
                            
                        
                        #make a list of lines to write to the data file
                        if mmode=='both':
                            if rpdict[station]['resxy'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                            fmt % lresxy +ss+fmt % lresxyerr+'\n')
                            if rpdict[station]['phasexy'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                            fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                            if rpdict[station]['resyx'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                            fmt % lresyx+ss+fmt % lresyxerr+'\n')
                            if rpdict[station]['phaseyx'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                            fmt % phaseyx+ss+fmt % dphaseyxerr+'\n')
                            if tippererr!=None and tipyn=='y':
                                if rpdict[station]['realtip'][0,jj-1]!=0.0:
                                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                                fmt % projtipr+ss+fmt % projtiperr+
                                                '\n')
                                if rpdict[station]['imagtip'][0,jj-1]!=0.0:
                                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                                fmt % projtipi+ss+fmt % projtiperr+
                                                '\n')
                        elif mmode=='TM':
                            if rpdict[station]['resyx'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                            fmt % lresyx +ss+fmt % lresyxerr+'\n')
                            if rpdict[station]['phaseyx'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                            fmt % phaseyx+ss+fmt % dphaseyxerr+'\n')
                            if tippererr!=None and tipyn=='y':
                                if rpdict[station]['realtip'][0,jj-1]!=0.0:
                                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                                fmt % projtipr+ss+fmt % projtiperr+
                                                '\n')
                                if rpdict[station]['imagtip'][0,jj-1]!=0.0:
                                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                                fmt % projtipi+ss+fmt % projtiperr+
                                                '\n')
                        elif mmode=='TE':
                            if rpdict[station]['resxy'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                            fmt % lresxy +ss+fmt % lresxyerr+'\n')
                            if rpdict[station]['phasexy'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                            fmt % phasexy+ss+fmt % dphasexyerr+'\n')
                            if tippererr!=None and tipyn=='y':
                                if rpdict[station]['realtip'][0,jj-1]!=0.0:
                                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                                fmt % projtipr+ss+fmt % projtiperr+
                                                '\n')
                                if rpdict[station]['imagtip'][0,jj-1]!=0.0:
                                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                                fmt % projtipi+ss+fmt % projtiperr+
                                                '\n')
                        else:
                            raise NameError('mmode' +mmode+' not defined')
                    except KeyError:
                        pass
        
        #If no rotation is desired but error bars are than...
        else:
            reslst=[]
            for kk,station in enumerate(stationlst,1):
                srp=rpdict[station]
                nr=srp['resxy'].shape[1]
                #calculate errors and rewrite
                #res_xy (TE)
                if resxyerr!=None:
                    if resxyerr=='prev':
                        lresxyerr=rpdict[station]['resxy'][1,:]
                    else:
                        lresxyerr=np.repeat((resxyerr/100.)/np.log(10),nr)
                    srp['resxy'][1,:]=lresxyerr
                
                #Res_yx(TM)
                if resyxerr!=None:
                    if resyxerr=='prev':
                        lresyxerr=rpdict[station]['resyx'][1,:]
                    else:
                        lresyxerr=np.repeat((resyxerr/100.)/np.log(10),nr)
                    srp['resyx'][1,:]=lresyxerr
                
                #phase_xy(TE)
                if phasexyerr!=None:
                    if phasexyerr=='prev':
                        dphasexyerr=rpdict[station]['phasexy'][1,:]
                    else:
                        dphasexyerr=np.repeat((phasexyerr/100.)*57/2.,nr)
                    srp['phasexy'][1,:]=dphasexyerr
                    
                #phase_yx (TM)
                if phaseyxerr!=None:
                    if phaseyxerr=='prev':
                        dphaseyxerr=rpdict[station]['phaseyx'][1,:]
                    else:
                        dphaseyxerr=np.repeat((phaseyxerr/100.)*57/2.,nr)
                    srp['phaseyx'][1,:]=dphaseyxerr
                
                if tippererr!=None:
                    #error of tipper is a decimal percentage
                    projtiperr=tippererr/100.
                    srp['realtip'][1,:]=np.repeat(projtiperr,nr)
                    srp['imagtip'][1,:]=np.repeat(projtiperr,nr)
                
                for jj,ff in enumerate(freq,1):
                    #make a list of lines to write to the data file
                    if mmode=='both':
                        if srp['resxy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                        fmt % srp['resxy'][0,jj-1]+ss+
                                        fmt % srp['resxy'][1,jj-1]+'\n')
                        if srp['phasexy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                        fmt % srp['phasexy'][0,jj-1]+ss+
                                        fmt % srp['phasexy'][1,jj-1]+'\n')
                        if srp['resyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                        fmt % srp['resyx'][0,jj-1]+ss+
                                        fmt % srp['resyx'][1,jj-1]+'\n')
                        if srp['phaseyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                        fmt % srp['phaseyx'][0,jj-1]+ss+
                                        fmt % srp['phaseyx'][1,jj-1]+'\n')
                        if tippererr!=None and tipyn=='y':
                            if srp['realtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                        fmt % srp['realtip'][0,jj-1]+ss+
                                        fmt % srp['realtip'][1,jj-1]+'\n')
                            if srp['imagtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                        fmt % srp['imagtip'][0,jj-1]+ss+
                                        fmt % srp['imagtip'][1,jj-1]+'\n')
                    elif mmode=='TM':
                        if srp['resyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                        fmt % srp['resyx'][0,jj-1]+ss+
                                        fmt % srp['resyx'][1,jj-1]+'\n')
                        if srp['phaseyx'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                        fmt % srp['phaseyx'][0,jj-1]+ss+
                                        fmt % srp['phaseyx'][1,jj-1]+'\n')
                        if tippererr!=None and tipyn=='y':
                            if srp['realtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                        fmt % srp['realtip'][0,jj-1]+ss+
                                        fmt % srp['realtip'][1,jj-1]+'\n')
                            if srp['imagtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                        fmt % srp['imagtip'][0,jj-1]+ss+
                                        fmt % srp['imagtip'][1,jj-1]+'\n')
                    elif mmode=='TE':
                        if srp['resxy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                        fmt % srp['resxy'][0,jj-1]+ss+
                                        fmt % srp['resxy'][1,jj-1]+'\n')
                        if srp['phasexy'][0,jj-1]!=0.0:
                            reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                        fmt % srp['phasexy'][0,jj-1]+ss+
                                        fmt % srp['phasexy'][1,jj-1]+'\n')
                        if tippererr!=None and tipyn=='y':
                            if srp['realtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                                        fmt % srp['realtip'][0,jj-1]+ss+
                                        fmt % srp['realtip'][1,jj-1]+'\n')
                            if srp['imagtip'][0,jj-1]!=0.0:
                                reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                                        fmt % srp['imagtip'][0,jj-1]+ss+
                                        fmt % srp['imagtip'][1,jj-1]+'\n')
    
        #===========================================================================
        #                             write dat file
        #===========================================================================
        
        #make the file name of the data file
        if self.datafn.find('RW')>0:
            self.ndatafn=self.datafn
        else:
            self.ndatafn=self.datafn[:-4]+'RW.dat'
            
        nstat=len(stationlst)
            
        if self.titlestr==None:
            self.titlestr='Occam Inversion'
            
        datfid=open(self.ndatafn,'w')
        datfid.write('FORMAT:'+' '*11+'OCCAM2MTDATA_1.0'+'\n')
        datfid.write('TITLE:'+' '*12+self.titlestr+'\n')
        
        #write station sites
        datfid.write('SITES:'+' '*12+str(nstat)+'\n')
        for station in stationlst:
            datfid.write(ss+station+'\n')
        
        #write offsets
        datfid.write('OFFSETS (M):'+'\n')
        for station in stationlst:
            datfid.write(ss+fmt % rpdict[station]['offset']+'\n')
        
        #write frequencies
        #writefreq=[freq[ff] for ff in range(0,len(freq),freqstep)]
        datfid.write('FREQUENCIES:'+' '*8+str(len(freq))+'\n')
        for ff in self.freq:
            datfid.write(ss+fmt % ff +'\n')
        
        #write data block
        datfid.write('DATA BLOCKS:'+' '*10+str(len(reslst))+'\n')
        datfid.write('SITE'+ss+'FREQ'+ss+'TYPE'+ss+'DATUM'+ss+'ERROR'+'\n')
        for ll,datline in enumerate(reslst):
            if datline.find('#IND')>=0:
                print 'Found #IND on line ',ll
                ndline=datline.replace('#IND','00')
                print 'Replaced with 00'
                datfid.write(ndline)
            else:
                datfid.write(datline)
        datfid.close()
        
        print 'Rewrote the data file to: ',self.ndatafn
    
    def plotMaskPoints(self,plottype=None,reserrinc=.20,phaseerrinc=5,
                       marker='o',colormode='color',dpi=300,ms=2,
                       reslimits=None,phaselimits=(-5,95)):
        """
        An interactive plotting tool to mask points an add errorbars
        """
        
        if colormode=='color':
            #color for data
            cted=(0,0,1)
            ctmd=(1,0,0)
            mted='s'
            mtmd='o'
            
        elif colormode=='bw':
            #color for data
            cted=(0,0,0)
            ctmd=(0,0,0)
            mted='s'
            mtmd='o'
            
        #read in data file    
        self.read2DdataFile()
        rplst=list(self.rplst)
        
        #get periods
        period=self.period
     
        #define some empty lists to put things into
        pstationlst=[]
        axlst=[]
        linelst=[]
        errlst=[]
        
        #get the stations to plot
        #if none plot all of them
        if plottype==None:
            pstationlst=range(len(self.stationlst))
            
        #otherwise pick out the stations to plot along with their index number
        elif type(plottype) is not list:
            plottype=[plottype]
            for ii,station in enumerate(self.stationlst):
                for pstation in plottype:
                    if station.find(pstation)>=0:
                        pstationlst.append(ii) 
        
        #set the subplot grid
        gs=gridspec.GridSpec(6,2,wspace=.1,left=.1,top=.93,bottom=.07)
        for jj,ii in enumerate(pstationlst):
            fig=plt.figure(ii+1,dpi=dpi)
            plt.clf()
            
            #make subplots
            axrte=fig.add_subplot(gs[:4,0])
            axrtm=fig.add_subplot(gs[:4,1])
            axpte=fig.add_subplot(gs[-2:,0],sharex=axrte)    
            axptm=fig.add_subplot(gs[-2:,1],sharex=axrtm)    
            
            
            #plot resistivity TE Mode
            #cut out missing data points first
            rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
            rte=axrte.errorbar(period[rxy],10**rplst[ii]['resxy'][0][rxy],
                            ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,
                            color=cted,
                            yerr=np.log(10)*rplst[ii]['resxy'][1][rxy]*\
                                10**rplst[ii]['resxy'][0][rxy],
                            ecolor=cted,picker=2)
                            
            #plot Phase TE Mode
            #cut out missing data points first
            pxy=[np.where(rplst[ii]['phasexy'][0]!=0)[0]]
            pte=axpte.errorbar(period[pxy],rplst[ii]['phasexy'][0][pxy],
                               ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,color=cted,
                               yerr=rplst[ii]['phasexy'][1][pxy],ecolor=cted,picker=1) 
            
                           
            #plot resistivity TM Mode
            #cut out missing data points first                
            ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
            rtm=axrtm.errorbar(period[ryx],10**rplst[ii]['resyx'][0][ryx],
                            ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,
                            color=ctmd,
                            yerr=np.log(10)*rplst[ii]['resyx'][1][ryx]*\
                                10**rplst[ii]['resyx'][0][ryx],
                            ecolor=ctmd,picker=2)
            #plot Phase TM Mode
            #cut out missing data points first
            pyx=[np.where(rplst[ii]['phaseyx'][0]!=0)[0]]
            ptm=axptm.errorbar(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                            ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,color=ctmd,
                            yerr=rplst[ii]['phaseyx'][1][pyx],ecolor=ctmd,picker=1)
        
        
            #make the axis presentable
            #set the apparent resistivity scales to log and x-axis to log
            axplst=[axrte,axrtm,axpte,axptm]
            llst=[rte[0],rtm[0],pte[0],ptm[0]]
            elst=[[rte[1][0],rte[1][1],rte[2][0]],[rtm[1][0],rtm[1][1],rtm[2][0]],
                [pte[1][0],pte[1][1],pte[2][0]],[ptm[1][0],ptm[1][1],ptm[2][0]]]
                
            axlst.append(axplst)
            linelst.append(llst)
            errlst.append(elst)
            
            #set the axes properties for each subplot
            for nn,xx in enumerate(axplst):
                #set xscale to logarithmic in period
                xx.set_xscale('log')
                
                #if apparent resistivity 
                if nn==0 or nn==1:
                    #set x-ticklabels to invisible
                    plt.setp(xx.xaxis.get_ticklabels(),visible=False)
                    
                    #set apparent resistivity scale to logarithmic
                    xx.set_yscale('log')
                    
                    #if there are resistivity limits set those
                    if reslimits!=None:
                        xx.set_ylim(reslimits)
                    
                #Set the title of the TE plot                 
                if nn==0:
                    xx.set_title(self.stationlst[ii]+' Obs$_{xy}$ (TE-Mode)',
                                 fontdict={'size':9,'weight':'bold'})
                    xx.yaxis.set_label_coords(-.075,.5)
                    xx.set_ylabel('App. Res. ($\Omega \cdot m$)',
                                  fontdict={'size':9,'weight':'bold'})
                #set the title of the TM plot
                if nn==1:
                    xx.set_title(self.stationlst[ii]+' Obs$_{yx}$ (TM-Mode)',
                                 fontdict={'size':9,'weight':'bold'})
                
                #set the phase axes properties
                if nn==2 or nn==3:
                    #set the phase limits
                    xx.set_ylim(phaselimits)
                    
                    #set label coordinates
                    xx.yaxis.set_label_coords(-.075,.5)
                    
                    #give the y-axis label to the bottom left plot
                    if nn==2:
                        xx.set_ylabel('Phase (deg)',
                                       fontdict={'size':9,'weight':'bold'})
                    #set the x-axis label
                    xx.set_xlabel('Period (s)',
                                  fontdict={'size':9,'weight':'bold'})
                    
                    #set tick marks of the y-axis
                    xx.yaxis.set_major_locator(MultipleLocator(10))
                    xx.yaxis.set_minor_locator(MultipleLocator(2))
                    
                xx.grid(True,alpha=.4,which='both') 
        
        #make points an attribute of self which is a data type OccamPointPicker       
        self.points=OccamPointPicker(axlst,linelst,errlst,reserrinc=reserrinc,
                                     phaseerrinc=phaseerrinc)
        
        #be sure to show the plot
        plt.show()
   
        
    def maskPoints(self):
        """
        maskPoints will take in points found from plotMaskPoints and rewrite 
        the data file to nameRW.dat.  Be sure to run plotMaskPoints first
        """
        
        self.read2DdataFile()
        rplst=list(self.rplst)
        #rewrite the data file
        #make a reverse dictionary for locating the masked points in the data file
        rploc=dict([('{0}'.format(self.points.fndict[key]),int(key)-1) 
                    for key in self.points.fndict.keys()])
                    
        #make a period dictionary to locate points changed
        frpdict=dict([('{0:.5g}'.format(fr),ff) 
                            for ff,fr in enumerate(1./self.freq)])
        
        #loop over the data list
        for dd,dat in enumerate(self.points.data):
            derror=self.points.error[dd]
            #loop over the 4 main entrie
            for ss,skey in enumerate(['resxy','resyx','phasexy','phaseyx']):
                #rewrite any coinciding points
                for frpkey in frpdict.keys():
                    try:
                        ff=frpdict[frpkey]
                        floc=self.points.fdict[dd][ss][frpkey]
                        
                        #CHANGE APPARENT RESISTIVITY
                        if ss==0 or ss==1:
                            #change the apparent resistivity value
                            if rplst[rploc[str(dd)]][skey][0][ff]!=\
                                                        np.log10(dat[ss][floc]):
                                if dat[ss][floc]==0:
                                    rplst[rploc[str(dd)]][skey][0][ff]=0.0
                                else:
                                    rplst[rploc[str(dd)]][skey][0][ff]=\
                                            np.log10(dat[ss][floc])
                                
                            #change the apparent resistivity error value
                            if dat[ss][floc]==0.0:
                                rerr=0.0
                            else:
                                rerr=derror[ss][floc]/dat[ss][floc]/np.log(10)
                            if rplst[rploc[str(dd)]][skey][1][ff]!=rerr:
                                rplst[rploc[str(dd)]][skey][1][ff]=rerr
                        
                        #DHANGE PHASE
                        elif ss==2 or ss==3:
                            #change the phase value
                            if rplst[rploc[str(dd)]][skey][0][ff]!=dat[ss][floc]:
                                if dat[ss][floc]==0:
                                    rplst[rploc[str(dd)]][skey][0][ff]=0.0
                                else:
                                    rplst[rploc[str(dd)]][skey][0][ff]=dat[ss][floc]
                                
                            #change the apparent resistivity error value
                            if dat[ss][floc]==0.0:
                                rerr=0.0
                            else:
                                rerr=derror[ss][floc]
                            if rplst[rploc[str(dd)]][skey][1][ff]!=rerr:
                                rplst[rploc[str(dd)]][skey][1][ff]=rerr
                    except KeyError:
                        pass
            
            
        #rewrite the data file 
        ss=3*' '
        fmt='%2.6f'
        reslst=[]
        
        #make a dictionary of rplst for easier extraction of data
        rpdict=dict([(station,rplst[ii]) for ii,station in enumerate(self.stationlst)])
        
        #loop over stations in the data file
        for kk,station in enumerate(self.stationlst,1):
            srp=rpdict[station]
            
            #loop over frequencies
            for jj,ff in enumerate(self.freq,1):
                #make a list of lines to write to the data file
                if srp['resxy'][0,jj-1]!=0.0:
                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'1'+ss+
                                fmt % srp['resxy'][0,jj-1]+ss+
                                fmt % srp['resxy'][1,jj-1]+'\n')
                if srp['phasexy'][0,jj-1]!=0.0:
                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'2'+ss+
                                fmt % srp['phasexy'][0,jj-1]+ss+
                                fmt % srp['phasexy'][1,jj-1]+'\n')
                if srp['resyx'][0,jj-1]!=0.0:
                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'5'+ss+
                                fmt % srp['resyx'][0,jj-1]+ss+
                                fmt % srp['resyx'][1,jj-1]+'\n')
                if srp['phaseyx'][0,jj-1]!=0.0:
                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'6'+ss+
                                fmt % srp['phaseyx'][0,jj-1]+ss+
                                fmt % srp['phaseyx'][1,jj-1]+'\n')
                if srp['realtip'][0,jj-1]!=0.0:
                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'3'+ss+
                            fmt % srp['realtip'][0,jj-1]+ss+
                            fmt % srp['realtip'][1,jj-1]+'\n')
                if srp['imagtip'][0,jj-1]!=0.0:
                    reslst.append(ss+str(kk)+ss+str(jj)+ss+'4'+ss+
                            fmt % srp['imagtip'][0,jj-1]+ss+
                            fmt % srp['imagtip'][1,jj-1]+'\n')
        
        #===========================================================================
        #                             write dat file
        #===========================================================================
        #make the file name of the data file
        if self.datafn.find('RW')>0:
            self.ndatafn=self.datafn
        else:
            self.ndatafn=self.datafn[:-4]+'RW.dat'
        
        #get number of stations
        nstat=len(self.stationlst)
        
        #set title string
        if self.titlestr==None:
            self.titlestr='Occam Inversion'
            
        datfid=open(self.ndatafn,'w')
        datfid.write('FORMAT:'+' '*11+'OCCAM2MTDATA_1.0'+'\n')
        datfid.write('TITLE:'+' '*12+self.titlestr+'\n')
        
        #write station sites
        datfid.write('SITES:'+' '*12+str(nstat)+'\n')
        for station in self.stationlst:
            datfid.write(ss+station+'\n')
        
        #write offsets
        datfid.write('OFFSETS (M):'+'\n')
        for station in self.stationlst:
            datfid.write(ss+fmt % rpdict[station]['offset']+'\n')
        
        #write frequencies
        #writefreq=[freq[ff] for ff in range(0,len(freq),freqstep)]
        datfid.write('FREQUENCIES:'+' '*8+str(len(self.freq))+'\n')
        for ff in self.freq:
            datfid.write(ss+fmt % ff +'\n')
        
        #write data block
        datfid.write('DATA BLOCKS:'+' '*10+str(len(reslst))+'\n')
        datfid.write('SITE'+ss+'FREQ'+ss+'TYPE'+ss+'DATUM'+ss+'ERROR'+'\n')
        for ll,datline in enumerate(reslst):
            if datline.find('#IND')>=0:
                print 'Found #IND on line ',ll
                ndline=datline.replace('#IND','00')
                print 'Replaced with 00'
                datfid.write(ndline)
            else:
                datfid.write(datline)
        datfid.close()
        
        print 'Wrote Occam2D data file to: ',self.ndatafn
    
    def read2DRespFile(self,respfn):
        """
        read2DRespFile will read in a response file and combine the data with info 
        from the data file.
    
        Input:
            respfn = full path to the response file
            datafn = full path to data file
    
        Outputs:
            for each data array, the rows are ordered as:
                0 -> input data
                1 -> input error
                2 -> model output
                3 -> relative error (data-model)/(input error)
                
            rplst = list of dictionaries for each station with keywords:
                'station' = station name
                'offset' = relative offset,
                'resxy' = TE resistivity 
                'resyx'= TM resistivity 
                'phasexy'= TE phase 
                'phaseyx'= TM phase a
                'realtip'= Real Tipper 
                'imagtip'= Imaginary Tipper 
                
                Note: that the resistivity will be in log10 space.  Also, there are
                2 extra rows in the data arrays, this is to put the response from
                the inversion. 
            
            stationlst = list of stations in order from one side of the profile
                         to the other.
            freq = list of frequencies used in the inversion
            title = title, could be useful for plotting.
            
        """
        #make the response file an attribute        
        self.respfn=respfn
        
        #read in the current data file
        self.read2DdataFile()
        
        rfid=open(self.respfn,'r')
        
        rlines=rfid.readlines()
        for line in rlines:
            ls=line.split()
            #station index
            ss=int(float(ls[0]))-1
            #component key
            comp=str(int(float(ls[2])))
            #frequency index        
            ff=int(float(ls[1]))-1
            #put into array
            #model response
            self.rplst[ss][occamdict[comp]][2,ff]=float(ls[5]) 
            #relative error        
            self.rplst[ss][occamdict[comp]][3,ff]=float(ls[6])
            
    def plot2DResponses(self,respfn=None,wlfn=None,maxcol=8,plottype='1',
                        ms=2,fs=10,phaselimits=(-5,95),colormode='color',
                        reslimits=None,plotnum=1,**kwargs):
        """
        plotResponse will plot the responses modeled from winglink against the 
        observed data.
        
        Inputs:
            respfn = full path to response file
            datafn = full path to data file
            wlfn = full path to a winglink data file used for a similar
                              inversion.  This will be plotted on the response
                              plots for comparison of fits.
            maxcol = maximum number of columns for the plot
            plottype = 'all' to plot all on the same plot
                       '1' to plot each respones in a different figure
                       station to plot a single station or enter as a list of 
                       stations to plot a few stations [station1,station2].  
                       Does not have to be verbatim but should have similar
                       unique characters input pb01 for pb01cs in outputfile
            ms = marker size 
            phaselimits = limits of phase in degrees (min,max)
            colormode = 'color' for color plots
                        'bw' for black and white plots
            reslimits = resistivity limits on a log scale (
                        log10(min),log10(max))
            plotnum = 1 to plot both TE and TM in the same plot
                      2 to plot TE and TM in separate subplots
                      
        """
        
        plt.rcParams['font.size']=fs-2
        
        try:
            dpi=kwargs['dpi']
        except KeyError:
            dpi=200
        
        #color mode
        if colormode=='color':
            #color for data
            cted=(0,0,1)
            ctmd=(1,0,0)
            mted='s'
            mtmd='o'
            
            #color for occam model
            ctem=(0,.6,.3)
            ctmm=(.9,0,.8)
            mtem='+'
            mtmm='+'
            
            #color for Winglink model
            ctewl=(0,.6,.8)
            ctmwl=(.8,.7,0)
            mtewl='x'
            mtmwl='x'
         
        #black and white mode
        elif colormode=='bw':
            #color for data
            cted=(0,0,0)
            ctmd=(0,0,0)
            mted='*'
            mtmd='v'
            
            #color for occam model
            ctem=(0.6,.6,.6)
            ctmm=(.6,.6,.6)
            mtem='+'
            mtmm='x'
            
            #color for Wingling model
            ctewl=(.3,.3,.3)
            ctmwl=(.3,.3,.3)    
            mtewl='|'
            mtmwl='_'
        
        #if there is a response file to plot
        if respfn!=None:
            #read in the data    
            self.read2DRespFile(respfn)
            #boolean for plotting response
            plotresp=True
        else:
            #read in current data file
            self.read2DdataFile()
            #boolean for plotting response
            plotresp=False
            
        #make a local copy of the rplst    
        rplst=list(self.rplst)
        
        #boolean for adding winglink output to the plots 0 for no, 1 for yes
        addwl=0
        hspace=.15
        #read in winglink data file
        if wlfn!=None:
            addwl=1
            hspace=.25
            wld,wlrplst,wlplst,wlslst,wltlst=wlt.readOutputFile(wlfn)
            sdict=dict([(ostation,wlstation) for wlstation in wlslst 
                        for ostation in self.stationlst 
                        if wlstation.find(ostation)>=0])
        
        #set a local parameter period for less typing
        period=self.period
                                          
        #---------------plot each respones in a different figure------------------
        if plottype=='1':
            
            #set the grid of subplots
            if plotnum==1:
                gs=gridspec.GridSpec(6,2,wspace=.1,left=.09,top=.93,bottom=.1,
                                     hspace=hspace)
            elif plotnum==2:
                gs=gridspec.GridSpec(6,2,wspace=.1,left=.07,top=.93,bottom=.1,
                                     hspace=hspace)
            #loop over each station
            for ii,station in enumerate(self.stationlst):
                
                rlst=[]
                llst=[]
                
#                rmslst=np.hstack((rplst[ii]['resxy'][3],
#                                           rplst[ii]['resyx'][3],
#                                            rplst[ii]['phasexy'][3],
#                                            rplst[ii]['phaseyx'][3]))
#                rms=np.sqrt(np.sum(ms**2 for ms in rmslst)/len(rmslst))
                #get the RMS values for each TE and TM modes separately
                rmslstte=np.hstack((rplst[ii]['resxy'][3],
                                    rplst[ii]['phasexy'][3]))
                rmslsttm=np.hstack((rplst[ii]['resyx'][3],
                                    rplst[ii]['phaseyx'][3]))
                rmste=np.sqrt(np.sum(rms**2 for rms in rmslstte)/len(rmslstte))
                rmstm=np.sqrt(np.sum(rms**2 for rms in rmslsttm)/len(rmslsttm))
                
                fig=plt.figure(ii+1,[9,10],dpi=dpi)
                plt.clf()
                
                #set subplot instances
                #plot both TE and TM in same subplot
                if plotnum==1:
                    axrte=fig.add_subplot(gs[:4,:])
                    axrtm=axrte
                    axpte=fig.add_subplot(gs[-2:,:],sharex=axrte)
                    axptm=axpte
                    
                #plot TE and TM in separate subplots
                elif plotnum==2:
                    axrte=fig.add_subplot(gs[:4,0])
                    axrtm=fig.add_subplot(gs[:4,1])
                    axpte=fig.add_subplot(gs[-2:,0],sharex=axrte)
                    axptm=fig.add_subplot(gs[-2:,1],sharex=axrtm)
                
                #Plot Resistivity
                
                #cut out missing data points first
                rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
                ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
                
                #check to see if there is a xy component (TE Mode)
                if len(rxy)>0:
                    rte=axrte.errorbar(period[rxy],
                                     10**rplst[ii]['resxy'][0][rxy],
                                    ls=':',marker=mted,ms=ms,mfc=cted,
                                    mec=cted,color=cted,
                                    yerr=np.log(10)*rplst[ii]['resxy'][1][rxy]*\
                                    10**rplst[ii]['resxy'][0][rxy],
                                    ecolor=cted,picker=2)
                    rlst.append(rte[0])
                    llst.append('$Obs_{TE}$')
                else:
                    pass
                
                #check to see if there is a yx component (TM Mode)
                if len(ryx)>0:
                    rtm=axrtm.errorbar(period[ryx],
                                       10**rplst[ii]['resyx'][0][ryx],
                                       ls=':',marker=mtmd,ms=ms,mfc=ctmd,
                                       mec=ctmd,color=ctmd,
                                       yerr=np.log(10)*rplst[ii]['resyx'][1][ryx]*\
                                       10**rplst[ii]['resyx'][0][ryx],
                                       ecolor=ctmd,picker=2)
                    rlst.append(rtm[0])
                    llst.append('$Obs_{TM}$')
                else:
                    pass                                
                
                
                #plot phase
                #cut out missing data points first
                pxy=np.where(rplst[ii]['phasexy'][0]!=0)[0]
                pyx=np.where(rplst[ii]['phaseyx'][0]!=0)[0]
                
                #plot the xy component (TE Mode)
                if len(pxy)>0:
                    axpte.errorbar(period[pxy],rplst[ii]['phasexy'][0][pxy],
                                 ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,
                                 color=cted,
                                 yerr=rplst[ii]['phasexy'][1][pxy],
                                 ecolor=cted,picker=1)
                else:
                    pass
                
                #plot the yx component (TM Mode)
                if len(pyx)>0:
                    axptm.errorbar(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                                 ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,
                                 color=ctmd,
                                 yerr=rplst[ii]['phaseyx'][1][pyx],
                                 ecolor=ctmd,picker=1)
                else:
                    pass
                
                #if there is a response file
                if plotresp==True:
                    mrxy=np.where(rplst[ii]['resxy'][2]!=0)[0]
                    mryx=np.where(rplst[ii]['resyx'][2]!=0)[0]
                    
                    #plot the Model Resistivity
                    #check for the xy of model component
                    if len(mrxy)>0:
                        r3=axrte.errorbar(period[mrxy],
                                          10**rplst[ii]['resxy'][2][mrxy],
                                          ls='--',marker=mtem,ms=ms,mfc=ctem,
                                          mec=ctem,color=ctem,
                                          yerr=10**(rplst[ii]['resxy'][3][mrxy]*\
                                          rplst[ii]['resxy'][2][mrxy]/np.log(10)),
                                          ecolor=ctem)
                        rlst.append(r3[0])
                        llst.append('$Mod_{TE}$')
                    else:
                        pass
                    
                    #check for the yx model component  of resisitivity
                    if len(mryx)>0:
                        r4=axrtm.errorbar(period[mryx],
                                          10**rplst[ii]['resyx'][2][mryx],
                                          ls='--',marker=mtmm,ms=ms,mfc=ctmm,
                                          mec=ctmm,color=ctmm,
                                          yerr=10**(rplst[ii]['resyx'][3][mryx]*\
                                          rplst[ii]['resyx'][2][mryx]/np.log(10)),
                                          ecolor=ctmm)
                        rlst.append(r4[0])
                        llst.append('$Mod_{TM}$')
                                    
                    #plot the model phase
                    #check for removed points
                    mpxy=np.where(rplst[ii]['phasexy'][2]!=0)[0]
                    mpyx=np.where(rplst[ii]['phaseyx'][2]!=0)[0]
                    
                    #plot the xy component (TE Mode)
                    if len(mpxy)>0:
                        axpte.errorbar(period[mpxy],
                                     rplst[ii]['phasexy'][2][mpxy],
                                     ls='--',marker=mtem,ms=ms,mfc=ctem,
                                     mec=ctem,color=ctem,
                                     yerr=rplst[ii]['phasexy'][3][mpxy],
                                     ecolor=ctem)
                    else:
                        pass
                    
                    #plot the yx component (TM Mode)
                    if len(mpyx)>0:
                        axptm.errorbar(period[mpyx],
                                     rplst[ii]['phaseyx'][2][mpyx],
                                     ls='--',marker=mtmm,ms=ms,mfc=ctmm,
                                     mec=ctmm, color=ctmm,
                                     yerr=rplst[ii]['phaseyx'][3][mpyx],
                                     ecolor=ctmm)
                    else:
                        pass
                             
                #add in winglink responses
                if addwl==1:
                    try:
                        wlrms=wld[sdict[station]]['rms']
                        axr.set_title(self.stationlst[ii]+'\n'+\
                                'rms_occ_TE={0:.2f}, rms_occ_TM={1:.2f}, rms_wl= {2:.2f}'.format(rmste,rmstm,wlrms),
                                     fontdict={'size':fs+1,'weight':'bold'})
                        for ww,wlstation in enumerate(wlslst):
    #                        print station,wlstation
                            if wlstation.find(station)==0:
                                print station,wlstation
                                wlrpdict=wlrplst[ww]
                        
                        zrxy=[np.where(wlrpdict['resxy'][0]!=0)[0]]
                        zryx=[np.where(wlrpdict['resyx'][0]!=0)[0]]
                        
                         #plot winglink resistivity
                        r5=axrte.loglog(wlplst[zrxy],
                                        wlrpdict['resxy'][1][zrxy],
                                        ls='-.',marker=mtewl,ms=5,color=ctewl,
                                        mfc=ctewl)
                        r6=axrtm.loglog(wlplst[zryx],
                                        wlrpdict['resyx'][1][zryx],
                                        ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                        mfc=ctmwl)
                        
                        #plot winglink phase
                        axpte.semilogx(wlplst[zrxy],
                                       wlrpdict['phasexy'][1][zrxy],
                                       ls='-.',marker=mtewl,ms=5,color=ctewl,
                                       mfc=ctewl)
                        axptm.semilogx(wlplst[zryx],
                                       wlrpdict['phaseyx'][1][zryx],
                                       ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                       mfc=ctmwl)
                        
                        rlst.append(r5[0])
                        rlst.append(r6[0])
                        llst.append('$WLMod_{TE}$')
                        llst.append('$WLMod_{TM}$')
                    except IndexError:
                        print 'Station not present'
                else:
                    if plotnum==1:
                        axrte.set_title(self.stationlst[ii]+\
                        ' rms_TE={0:.2f}, rms_TM={1:.2f}'.format(rmste,rmstm),
                                  fontdict={'size':fs+1,'weight':'bold'})
                    elif plotnum==2:
                        axrte.set_title(self.stationlst[ii]+\
                                        ' rms_TE={0:.2f}'.format(rmste),
                                        fontdict={'size':fs+1,'weight':'bold'})
                        axrtm.set_title(self.stationlst[ii]+\
                                        ' rms_TM={0:.2f}'.format(rmstm),
                                        fontdict={'size':fs+1,'weight':'bold'})
                
                #set the axis properties
                for aa,axr in enumerate([axrte,axrtm]):
                    #set both axes to logarithmic scale
                    axr.set_xscale('log')
                    axr.set_yscale('log')
                    
                    #put on a grid
                    axr.grid(True,alpha=.3,which='both')
                    axr.yaxis.set_label_coords(-.07,.5)
                    
                    #set resistivity limits if desired
                    if reslimits!=None:
                        axr.set_ylim(10**reslimits[0],10**reslimits[1])
                        
                    #set the tick labels to invisible
                    plt.setp(axr.xaxis.get_ticklabels(),visible=False)
                    if aa==0:
                        axr.set_ylabel('App. Res. ($\Omega \cdot m$)',
                               fontdict={'size':fs,'weight':'bold'})
                               
                    #set legend based on the plot type
                    if plotnum==1:
                        if aa==0:
                            axr.legend(rlst,llst,
                                       loc=2,markerscale=1,
                                       borderaxespad=.05,
                                       labelspacing=.08,
                                       handletextpad=.15,
                                       borderpad=.05,
                                       prop={'size':fs})
                    elif plotnum==2:
                        if aa==0:
                            if plotresp==True:
                                try:
                                    axr.legend([rlst[0],rlst[2]],
                                               [llst[0],llst[2]],
                                               loc=2,markerscale=1,
                                               borderaxespad=.05,
                                               labelspacing=.08,
                                               handletextpad=.15,
                                               borderpad=.05,
                                               prop={'size':fs}) 
                                except IndexError:
                                    pass
                                               
                            else:
                                try:
                                    axr.legend([rlst[0]],[llst[0]],
                                               loc=2,markerscale=1,
                                               borderaxespad=.05,
                                               labelspacing=.08,
                                               handletextpad=.15,
                                               borderpad=.05,
                                               prop={'size':fs})
                                except IndexError:
                                    pass
                        if aa==1:
                            if plotresp==True:
                                try:
                                    axr.legend([rlst[1],rlst[3]],
                                               [llst[1],llst[3]],
                                               loc=2,markerscale=1,
                                               borderaxespad=.05,
                                               labelspacing=.08,
                                               handletextpad=.15
                                               ,borderpad=.05,
                                               prop={'size':fs})
                                except IndexError:
                                    pass
                            else:
                                try:
                                    axr.legend([rlst[1]],[llst[1]],
                                               loc=2,markerscale=1,
                                               borderaxespad=.05,
                                               labelspacing=.08,
                                               handletextpad=.15,
                                               borderpad=.05,
                                               prop={'size':fs})    
                                except IndexError:
                                    pass
                
                #set Properties for the phase axes
                for aa,axp in enumerate([axpte,axptm]):
                    #set the x-axis to log scale
                    axp.set_xscale('log')
                    
                    #set the phase limits
                    axp.set_ylim(phaselimits)
                    
                    #put a grid on the subplot
                    axp.grid(True,alpha=.3,which='both')
                    
                    #set the tick locations
                    axp.yaxis.set_major_locator(MultipleLocator(10))
                    axp.yaxis.set_minor_locator(MultipleLocator(2))
                    
                    #set the x axis label
                    axp.set_xlabel('Period (s)',
                                   fontdict={'size':fs,'weight':'bold'})
                    
                    #put the y label on the far left plot
                    axp.yaxis.set_label_coords(-.07,.5)
                    if aa==0:
                        axp.set_ylabel('Phase (deg)',
                                       fontdict={'size':fs,'weight':'bold'})
                    
                
        #---Plot single or subset of stations-------------------------------------
        else:
            pstationlst=[]
    
            if type(plottype) is not list:
                plottype=[plottype]
            for ii,station in enumerate(self.stationlst):
                for pstation in plottype:
                    if station.find(pstation)>=0:
    #                    print 'plotting ',station
                        pstationlst.append(ii)
            if addwl==1:
                pwlstationlst=[]
                for ww,wlstation in enumerate(wlslst):
                    for pstation in plottype:
                        if wlstation.find(pstation)>=0:
    #                        print 'plotting ',wlstation
                            pwlstationlst.append(ww)  
            if plotnum==1:
                gs=gridspec.GridSpec(6,2,wspace=.1,left=.09,top=.93,bottom=.1,
                                     hspace=hspace)
            elif plotnum==2:
                gs=gridspec.GridSpec(6,2,wspace=.1,left=.07,top=.93,bottom=.1,
                                     hspace=hspace)
            for jj,ii in enumerate(pstationlst):
                rlst=[]
                llst=[]
                
                #get RMS values for TE and TM separately
                rmslstte=np.hstack((rplst[ii]['resxy'][3],
                                    rplst[ii]['phasexy'][3]))
                rmslsttm=np.hstack((rplst[ii]['resyx'][3],
                                    rplst[ii]['phaseyx'][3]))
                rmste=np.sqrt(np.sum(rms**2 for rms in rmslstte)/len(rmslstte))
                rmstm=np.sqrt(np.sum(rms**2 for rms in rmslsttm)/len(rmslsttm))
                
                
                fig=plt.figure(ii+1,[9,10],dpi=dpi)
                plt.clf()
                
                #set subplot instances
                #plot both TE and TM in same subplot
                if plotnum==1:
                    axrte=fig.add_subplot(gs[:4,:])
                    axrtm=axrte
                    axpte=fig.add_subplot(gs[-2:,:],sharex=axrte)
                    axptm=axpte
                    
                #plot TE and TM in separate subplots
                elif plotnum==2:
                    axrte=fig.add_subplot(gs[:4,0])
                    axrtm=fig.add_subplot(gs[:4,1])
                    axpte=fig.add_subplot(gs[-2:,0],sharex=axrte)
                    axptm=fig.add_subplot(gs[-2:,1],sharex=axrtm)
                
                #Plot Resistivity
                
                #cut out missing data points first
                rxy=np.where(rplst[ii]['resxy'][0]!=0)[0]
                ryx=np.where(rplst[ii]['resyx'][0]!=0)[0]
                
                #check to see if there is a xy component (TE Mode)
                if len(rxy)>0:
                    rte=axrte.errorbar(period[rxy],
                                     10**rplst[ii]['resxy'][0][rxy],
                                    ls=':',marker=mted,ms=ms,mfc=cted,
                                    mec=cted,color=cted,
                                    yerr=np.log(10)*rplst[ii]['resxy'][1][rxy]*\
                                    10**rplst[ii]['resxy'][0][rxy],
                                    ecolor=cted,picker=2)
                    rlst.append(rte[0])
                    llst.append('$Obs_{TE}$')
                else:
                    pass
                
                #check to see if there is a yx component (TM Mode)
                if len(ryx)>0:
                    rtm=axrtm.errorbar(period[ryx],
                                       10**rplst[ii]['resyx'][0][ryx],
                                       ls=':',marker=mtmd,ms=ms,mfc=ctmd,
                                       mec=ctmd,color=ctmd,
                                       yerr=np.log(10)*rplst[ii]['resyx'][1][ryx]*\
                                       10**rplst[ii]['resyx'][0][ryx],
                                       ecolor=ctmd,picker=2)
                    rlst.append(rtm[0])
                    llst.append('$Obs_{TM}$')
                else:
                    pass                                
                
                
                #plot phase
                #cut out missing data points first
                pxy=np.where(rplst[ii]['phasexy'][0]!=0)[0]
                pyx=np.where(rplst[ii]['phaseyx'][0]!=0)[0]
                
                #plot the xy component (TE Mode)
                if len(pxy)>0:
                    axpte.errorbar(period[pxy],rplst[ii]['phasexy'][0][pxy],
                                 ls=':',marker=mted,ms=ms,mfc=cted,mec=cted,
                                 color=cted,
                                 yerr=rplst[ii]['phasexy'][1][pxy],
                                 ecolor=cted,picker=1)
                else:
                    pass
                
                #plot the yx component (TM Mode)
                if len(pyx)>0:
                    axptm.errorbar(period[pyx],rplst[ii]['phaseyx'][0][pyx],
                                 ls=':',marker=mtmd,ms=ms,mfc=ctmd,mec=ctmd,
                                 color=ctmd,
                                 yerr=rplst[ii]['phaseyx'][1][pyx],
                                 ecolor=ctmd,picker=1)
                else:
                    pass
                
                #if there is a response file
                if plotresp==True:
                    mrxy=np.where(rplst[ii]['resxy'][2]!=0)[0]
                    mryx=np.where(rplst[ii]['resyx'][2]!=0)[0]
                    
                    #plot the Model Resistivity
                    #check for the xy of model component
                    if len(mrxy)>0:
                        r3=axrte.errorbar(period[mrxy],
                                          10**rplst[ii]['resxy'][2][mrxy],
                                          ls='--',marker=mtem,ms=ms,mfc=ctem,
                                          mec=ctem,color=ctem,
                                          yerr=10**(rplst[ii]['resxy'][3][mrxy]*\
                                          rplst[ii]['resxy'][2][mrxy]/np.log(10)),
                                          ecolor=ctem)
                        rlst.append(r3[0])
                        llst.append('$Mod_{TE}$')
                    else:
                        pass
                    
                    #check for the yx model component  of resisitivity
                    if len(mryx)>0:
                        r4=axrtm.errorbar(period[mryx],
                                          10**rplst[ii]['resyx'][2][mryx],
                                          ls='--',marker=mtmm,ms=ms,mfc=ctmm,
                                          mec=ctmm,color=ctmm,
                                          yerr=10**(rplst[ii]['resyx'][3][mryx]*\
                                          rplst[ii]['resyx'][2][mryx]/np.log(10)),
                                          ecolor=ctmm)
                        rlst.append(r4[0])
                        llst.append('$Mod_{TM}$')
                                    
                    #plot the model phase
                    #check for removed points
                    mpxy=np.where(rplst[ii]['phasexy'][2]!=0)[0]
                    mpyx=np.where(rplst[ii]['phaseyx'][2]!=0)[0]
                    
                    #plot the xy component (TE Mode)
                    if len(mpxy)>0:
                        axpte.errorbar(period[mpxy],
                                     rplst[ii]['phasexy'][2][mpxy],
                                     ls='--',marker=mtem,ms=ms,mfc=ctem,
                                     mec=ctem,color=ctem,
                                     yerr=rplst[ii]['phasexy'][3][mpxy],
                                     ecolor=ctem)
                    else:
                        pass
                    
                    #plot the yx component (TM Mode)
                    if len(mpyx)>0:
                        axptm.errorbar(period[mpyx],
                                     rplst[ii]['phaseyx'][2][mpyx],
                                     ls='--',marker=mtmm,ms=ms,mfc=ctmm,
                                     mec=ctmm, color=ctmm,
                                     yerr=rplst[ii]['phaseyx'][3][mpyx],
                                     ecolor=ctmm)
                    else:
                        pass
                             
                #add in winglink responses
                if addwl==1:
                    try:
                        wlrms=wld[sdict[station]]['rms']
                        axr.set_title(stationlst[ii]+'\n'+\
                                    ' rms_occ_TE={0:.2f}, rms_occ_TM={1:.2f}, rms_wl= {2:.2f}'.format(rmste,rmstm,wlrms),
                                     fontdict={'size':fs+1,'weight':'bold'})
                        for ww,wlstation in enumerate(wlslst):
    #                        print station,wlstation
                            if wlstation.find(station)==0:
                                print station,wlstation
                                wlrpdict=wlrplst[ww]
                        
                        zrxy=[np.where(wlrpdict['resxy'][0]!=0)[0]]
                        zryx=[np.where(wlrpdict['resyx'][0]!=0)[0]]
                        
                         #plot winglink resistivity
                        r5=axrte.loglog(wlplst[zrxy],
                                        wlrpdict['resxy'][1][zrxy],
                                        ls='-.',marker=mtewl,ms=5,color=ctewl,
                                        mfc=ctewl)
                        r6=axrtm.loglog(wlplst[zryx],
                                        wlrpdict['resyx'][1][zryx],
                                        ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                        mfc=ctmwl)
                        
                        #plot winglink phase
                        axpte.semilogx(wlplst[zrxy],
                                       wlrpdict['phasexy'][1][zrxy],
                                       ls='-.',marker=mtewl,ms=5,color=ctewl,
                                       mfc=ctewl)
                        axptm.semilogx(wlplst[zryx],
                                       wlrpdict['phaseyx'][1][zryx],
                                       ls='-.',marker=mtmwl,ms=5,color=ctmwl,
                                       mfc=ctmwl)
                        
                        rlst.append(r5[0])
                        rlst.append(r6[0])
                        llst.append('$WLMod_{TE}$')
                        llst.append('$WLMod_{TM}$')
                    except IndexError:
                        print 'Station not present'
                else:
                    if plotnum==1:
                        axrte.set_title(self.stationlst[ii]+\
                        ' rms_TE={0:.2f}, rms_TM={1:.2f}'.format(rmste,rmstm),
                                  fontdict={'size':fs+1,'weight':'bold'})
                    elif plotnum==2:
                        axrte.set_title(self.stationlst[ii]+\
                                        ' rms_TE={0:.2f}'.format(rmste),
                                        fontdict={'size':fs+1,'weight':'bold'})
                        axrtm.set_title(self.stationlst[ii]+\
                                        ' rms_TM={0:.2f}'.format(rmstm),
                                        fontdict={'size':fs+1,'weight':'bold'})
                
                
                #set the axis properties
                for aa,axr in enumerate([axrte,axrtm]):
                    #set both axes to logarithmic scale
                    axr.set_xscale('log')
                    axr.set_yscale('log')
                    
                    #put on a grid
                    axr.grid(True,alpha=.3,which='both')
                    axr.yaxis.set_label_coords(-.07,.5)
                    
                    #set resistivity limits if desired
                    if reslimits!=None:
                        axr.set_ylim(10**reslimits[0],10**reslimits[1])
                        
                    #set the tick labels to invisible
                    plt.setp(axr.xaxis.get_ticklabels(),visible=False)
                    if aa==0:
                        axr.set_ylabel('App. Res. ($\Omega \cdot m$)',
                               fontdict={'size':fs,'weight':'bold'})
                    if plotnum==1:
                        if aa==0:
                            axr.legend(rlst,llst,
                               loc=2,markerscale=1,borderaxespad=.05,
                               labelspacing=.08,
                               handletextpad=.15,borderpad=.05,prop={'size':fs})
                    elif plotnum==2:
                        if aa==0:
                            if plotresp==True:
                                axr.legend([rlst[0],rlst[2]],[llst[0],llst[2]],
                                   loc=2,markerscale=1,borderaxespad=.05,
                                   labelspacing=.08,
                                   handletextpad=.15,borderpad=.05,
                                   prop={'size':fs}) 
                            else:
                                axr.legend([rlst[0]],[llst[0]],
                                   loc=2,markerscale=1,borderaxespad=.05,
                                   labelspacing=.08,
                                   handletextpad=.15,borderpad=.05,
                                   prop={'size':fs})
                        if aa==1:
                            if plotresp==True:
                                axr.legend([rlst[1],rlst[3]],[llst[1],llst[3]],
                                   loc=2,markerscale=1,borderaxespad=.05,
                                   labelspacing=.08,
                                   handletextpad=.15,borderpad=.05,
                                   prop={'size':fs}) 
                            else:
                                axr.legend([rlst[1]],[llst[1]],
                                   loc=2,markerscale=1,borderaxespad=.05,
                                   labelspacing=.08,
                                   handletextpad=.15,borderpad=.05,
                                   prop={'size':fs})
                
                for aa,axp in enumerate([axpte,axptm]):
                    #set the x-axis to log scale
                    axp.set_xscale('log')
                    
                    #set the phase limits
                    axp.set_ylim(phaselimits)
                    
                    #put a grid on the subplot
                    axp.grid(True,alpha=.3,which='both')
                    
                    #set the tick locations
                    axp.yaxis.set_major_locator(MultipleLocator(10))
                    axp.yaxis.set_minor_locator(MultipleLocator(2))
                    
                    #set the x axis label
                    axp.set_xlabel('Period (s)',
                                   fontdict={'size':fs,'weight':'bold'})
                    
                    #put the y label on the far left plot
                    axp.yaxis.set_label_coords(-.07,.5)
                    if aa==0:
                        axp.set_ylabel('Phase (deg)',
                                       fontdict={'size':fs,'weight':'bold'})
    
    
    def plotPseudoSection(self,respfn=None,fignum=1,rcmap='jet_r',pcmap='jet',
                      rlim=((0,4),(0,4)),plim=((0,90),(0,90)),ml=2,
                      stationid=[0,4]):
        """
        plots a pseudo section of the data
        
        datafn = full path to data file
        respfn = full path to response file
        """
        
        try:
            self.read2DRespFile(respfn)
            nr=2
        except TypeError:
            nr=1
        
        ns=len(self.stationlst)
        nf=len(self.freq)
        ylimits=(1./self.freq.min(),1./self.freq.max())
    #    print ylimits
        
        #make a grid for pcolormesh so you can have a log scale
        #get things into arrays for plotting
        offsetlst=np.zeros(ns)
        resxyarr=np.zeros((nf,ns,nr))    
        resyxarr=np.zeros((nf,ns,nr))    
        phasexyarr=np.zeros((nf,ns,nr))    
        phaseyxarr=np.zeros((nf,ns,nr))
    
        for ii,rpdict in enumerate(self.rplst):
            offsetlst[ii]=rpdict['offset']     
            resxyarr[:,ii,0]=rpdict['resxy'][0]
            resyxarr[:,ii,0]=rpdict['resyx'][0]
            phasexyarr[:,ii,0]=rpdict['phasexy'][0]
            phaseyxarr[:,ii,0]=rpdict['phaseyx'][0]
            if respfn!=None:
                resxyarr[:,ii,1]=rpdict['resxy'][2]
                resyxarr[:,ii,1]=rpdict['resyx'][2]
                phasexyarr[:,ii,1]=rpdict['phasexy'][2]
                phaseyxarr[:,ii,1]=rpdict['phaseyx'][2]
                
                
        #make a meshgrid for plotting
        #flip frequency so bottom corner is long period
        dgrid,fgrid=np.meshgrid(offsetlst,1./self.freq[::-1])
    
        #make list for station labels
        slabel=[self.stationlst[ss][stationid[0]:stationid[1]] 
                    for ss in range(0,ns,ml)]
        labellst=['$r_{TE-Data}$','$r_{TE-Model}$',
                  '$r_{TM-Data}$','$r_{TM-Model}$',
                  '$\phi_{TE-Data}$','$\phi_{TE-Model}$',
                  '$\phi_{TM-Data}$','$\phi_{TM-Model}$']
        xloc=offsetlst[0]+abs(offsetlst[0]-offsetlst[1])/5
        yloc=1./self.freq[1]
        
        if respfn!=None:

            plt.rcParams['font.size']=7
            plt.rcParams['figure.subplot.bottom']=.09
            plt.rcParams['figure.subplot.top']=.96        
            
            fig=plt.figure(fignum,dpi=200)
            plt.clf()
            gs1=gridspec.GridSpec(2,2,left=0.06,right=.48,hspace=.1,wspace=.005)
            gs2=gridspec.GridSpec(2,2,left=0.52,right=.98,hspace=.1,wspace=.005)
            
            ax1r=fig.add_subplot(gs1[0,0])
            ax1r.pcolormesh(dgrid,fgrid,np.flipud(resxyarr[:,:,0]),cmap=rcmap,
                           vmin=rlim[0][0],vmax=rlim[0][1])
            
            ax2r=fig.add_subplot(gs1[0,1])
            ax2r.pcolormesh(dgrid,fgrid,np.flipud(resxyarr[:,:,1]),cmap=rcmap,
                           vmin=rlim[0][0],vmax=rlim[0][1])
                           
            ax3r=fig.add_subplot(gs2[0,0])
            ax3r.pcolormesh(dgrid,fgrid,np.flipud(resyxarr[:,:,0]),cmap=rcmap,
                           vmin=rlim[1][0],vmax=rlim[1][1])
            
            ax4r=fig.add_subplot(gs2[0,1])
            ax4r.pcolormesh(dgrid,fgrid,np.flipud(resyxarr[:,:,1]),cmap=rcmap,
                           vmin=rlim[1][0],vmax=rlim[1][1])
    
            ax1p=fig.add_subplot(gs1[1,0])
            ax1p.pcolormesh(dgrid,fgrid,np.flipud(phasexyarr[:,:,0]),cmap=pcmap,
                           vmin=plim[0][0],vmax=plim[0][1])
            
            ax2p=fig.add_subplot(gs1[1,1])
            ax2p.pcolormesh(dgrid,fgrid,np.flipud(phasexyarr[:,:,1]),cmap=pcmap,
                           vmin=plim[0][0],vmax=plim[0][1])
                           
            ax3p=fig.add_subplot(gs2[1,0])
            ax3p.pcolormesh(dgrid,fgrid,np.flipud(phaseyxarr[:,:,0]),cmap=pcmap,
                           vmin=plim[1][0],vmax=plim[1][1])
            
            ax4p=fig.add_subplot(gs2[1,1])
            ax4p.pcolormesh(dgrid,fgrid,np.flipud(phaseyxarr[:,:,1]),cmap=pcmap,
                           vmin=plim[1][0],vmax=plim[1][1])
            
            axlst=[ax1r,ax2r,ax3r,ax4r,ax1p,ax2p,ax3p,ax4p]
            
            for xx,ax in enumerate(axlst):
                ax.semilogy()
                ax.set_ylim(ylimits)
                ax.xaxis.set_ticks(offsetlst[np.arange(0,ns,ml)])
                ax.xaxis.set_ticks(offsetlst,minor=True)
                ax.xaxis.set_ticklabels(slabel)
                ax.set_xlim(offsetlst.min(),offsetlst.max())
                if np.remainder(xx,2.0)==1:
                    plt.setp(ax.yaxis.get_ticklabels(),visible=False)
                    cbx=mcb.make_axes(ax,shrink=.7,pad=.015)
                    if xx<4:
                        if xx==1:
                            cb=mcb.ColorbarBase(cbx[0],cmap=rcmap,
                                            norm=Normalize(vmin=rlim[0][0],
                                                           vmax=rlim[0][1]))
                        if xx==3:
                            cb=mcb.ColorbarBase(cbx[0],cmap=rcmap,
                                            norm=Normalize(vmin=rlim[1][0],
                                                           vmax=rlim[1][1]))
                            cb.set_label('App. Res. ($\Omega \cdot$m)',
                                         fontdict={'size':9})
                    else:
                        if xx==5:
                            cb=mcb.ColorbarBase(cbx[0],cmap=pcmap,
                                            norm=Normalize(vmin=plim[0][0],
                                                           vmax=plim[0][1]))
                        if xx==7:
                            cb=mcb.ColorbarBase(cbx[0],cmap=pcmap,
                                            norm=Normalize(vmin=plim[1][0],
                                                           vmax=plim[1][1]))
                            cb.set_label('Phase (deg)',fontdict={'size':9})
                ax.text(xloc,yloc,labellst[xx],
                        fontdict={'size':10},
                        bbox={'facecolor':'white'},
                        horizontalalignment='left',
                        verticalalignment='top')
                if xx==0 or xx==4:
                    ax.set_ylabel('Period (s)',
                                  fontdict={'size':10,'weight':'bold'})
                if xx>3:
                    ax.set_xlabel('Station',fontdict={'size':10,
                                                      'weight':'bold'})
                
                    
            plt.show()
            
        else:

            plt.rcParams['font.size']=7
            plt.rcParams['figure.subplot.bottom']=.09
            plt.rcParams['figure.subplot.top']=.96        
            
            fig=plt.figure(fignum,dpi=200)
            plt.clf()
            gs1=gridspec.GridSpec(2,2,left=0.06,right=.48,hspace=.1,
                                  wspace=.005)
            gs2=gridspec.GridSpec(2,2,left=0.52,right=.98,hspace=.1,
                                  wspace=.005)
            
            ax1r=fig.add_subplot(gs1[0,:])
            ax1r.pcolormesh(dgrid,fgrid,np.flipud(resxyarr[:,:,0]),cmap=rcmap,
                           vmin=rlim[0][0],vmax=rlim[0][1])
            
                           
            ax3r=fig.add_subplot(gs2[0,:])
            ax3r.pcolormesh(dgrid,fgrid,np.flipud(resyxarr[:,:,0]),cmap=rcmap,
                           vmin=rlim[1][0],vmax=rlim[1][1])
            
    
            ax1p=fig.add_subplot(gs1[1,:])
            ax1p.pcolormesh(dgrid,fgrid,np.flipud(phasexyarr[:,:,0]),cmap=pcmap,
                           vmin=plim[0][0],vmax=plim[0][1])
            
                           
            ax3p=fig.add_subplot(gs2[1,:])
            ax3p.pcolormesh(dgrid,fgrid,np.flipud(phaseyxarr[:,:,0]),cmap=pcmap,
                           vmin=plim[1][0],vmax=plim[1][1])
            
            
            axlst=[ax1r,ax3r,ax1p,ax3p]
            
            for xx,ax in enumerate(axlst):
                ax.semilogy()
                ax.set_ylim(ylimits)
                ax.xaxis.set_ticks(offsetlst[np.arange(0,ns,ml)])
                ax.xaxis.set_ticks(offsetlst,minor=True)
                ax.xaxis.set_ticklabels(slabel)
                ax.set_xlim(offsetlst.min(),offsetlst.max())
                plt.setp(ax.yaxis.get_ticklabels(),visible=False)
                cbx=mcb.make_axes(ax,shrink=.7,pad=.015)
                if xx==0:
                    cb=mcb.ColorbarBase(cbx[0],cmap=rcmap,
                                    norm=Normalize(vmin=rlim[0][0],
                                                   vmax=rlim[0][1]))
                elif xx==1:
                    cb=mcb.ColorbarBase(cbx[0],cmap=rcmap,
                                    norm=Normalize(vmin=rlim[1][0],
                                                   vmax=rlim[1][1]))
                    cb.set_label('App. Res. ($\Omega \cdot$m)',
                                 fontdict={'size':9})
                elif xx==2:
                    cb=mcb.ColorbarBase(cbx[0],cmap=pcmap,
                                    norm=Normalize(vmin=plim[0][0],
                                                   vmax=plim[0][1]))
                elif xx==3:
                    cb=mcb.ColorbarBase(cbx[0],cmap=pcmap,
                                    norm=Normalize(vmin=plim[1][0],
                                                   vmax=plim[1][1]))
                    cb.set_label('Phase (deg)',fontdict={'size':9})
                ax.text(xloc,yloc,labellst[xx],
                        fontdict={'size':10},
                        bbox={'facecolor':'white'},
                        horizontalalignment='left',
                        verticalalignment='top')
                if xx==0 or xx==2:
                    ax.set_ylabel('Period (s)',
                                  fontdict={'size':10,'weight':'bold'})
                if xx>1:
                    ax.set_xlabel('Station',fontdict={'size':10,
                                                      'weight':'bold'})
                
                    
            plt.show()
    
    def plotAllResponses(self,station,fignum=1):
        """
        Plot all the responses of occam inversion from data file.  This assumes
        the response curves are in the same folder as the datafile.
    
        Input:
            datafile = full path to occam data file
            
        Output:
            Plot
        
        """    
        
        rpath=os.path.dirname(self.datafn)
        
        gs=gridspec.GridSpec(6,2,wspace=.20)
        
        plt.rcParams['font.size']=int(7)
        plt.rcParams['figure.subplot.left']=.08
        plt.rcParams['figure.subplot.right']=.98
        plt.rcParams['figure.subplot.bottom']=.1
        plt.rcParams['figure.subplot.top']=.92
    
    
        rlst=[os.path.join(rpath,rfile) for rfile in os.listdir(rpath) 
                if rfile.find('.resp')>0]
        
        nresp=len(rlst)
        
        colorlst=[(cc,0,1-cc) for cc in np.arange(0,1,1./nresp)]
        fig=plt.figure(fignum,[7,8],dpi=200)
        plt.clf()
        axrte=fig.add_subplot(gs[:4,0])
        axrtm=fig.add_subplot(gs[:4,1])
        axpte=fig.add_subplot(gs[-2:,0])
        axptm=fig.add_subplot(gs[-2:,1])
        rmstelst=[]
        rmstmlst=[]
        rmstestr=[]
        rmstmstr=[]
        #read responses
        for jj,rfile in enumerate(rlst):
            respfn=os.path.join(rpath,rfile)
            self.read2DRespFile(respfn)
            
            ii=np.where(np.array(self.stationlst)==station)[0][0]
            
            period=1./self.freq
            
            rmslstte=np.hstack((self.rplst[ii]['resxy'][3],
                                self.rplst[ii]['phasexy'][3]))
            rmslsttm=np.hstack((self.rplst[ii]['resyx'][3],
                                self.rplst[ii]['phaseyx'][3]))
            rmste=np.sqrt(np.sum(ms**2 for ms in rmslstte)/len(rmslstte))
            rmstm=np.sqrt(np.sum(ms**2 for ms in rmslsttm)/len(rmslsttm))
            rmstelst.append('%d rms=%.3f ' % (jj,rmste))
            rmstmlst.append('%d rms=%.3f ' % (jj,rmstm))
            rmstestr.append(rmste)
            rmstmstr.append(rmstm)
            #plot resistivity
            
            
            if jj==0:
                #cut out missing data points first
                rxy=np.where(self.rplst[ii]['resxy'][0]!=0)[0]
                ryx=np.where(self.rplst[ii]['resyx'][0]!=0)[0]
                r1,=axrte.loglog(period[rxy],
                                 10**self.rplst[ii]['resxy'][0][rxy],
                                 ls=':',marker='s',ms=4,color='k',mfc='k')
                r2,=axrtm.loglog(period[ryx],
                                 10**self.rplst[ii]['resyx'][0][ryx],
                                 ls=':',marker='o',ms=4,color='k',mfc='k')
                rlstte=[r1]
                rlsttm=[r2]
        
            mrxy=[np.where(self.rplst[ii]['resxy'][2]!=0)[0]]
            mryx=[np.where(self.rplst[ii]['resyx'][2]!=0)[0]]
            r3,=axrte.loglog(period[mrxy],10**self.rplst[ii]['resxy'][2][mrxy],
                            ls='-',color=colorlst[jj])
            r4,=axrtm.loglog(period[mryx],10**self.rplst[ii]['resyx'][2][mryx],
                            ls='-',color=colorlst[jj])
        
            rlstte.append(r3)
            rlsttm.append(r4)
                                
            #plot phase
            #cut out missing data points first
            pxy=[np.where(self.rplst[ii]['phasexy'][0]!=0)[0]]
            pyx=[np.where(self.rplst[ii]['phaseyx'][0]!=0)[0]]
            
            if jj==0:            
                axpte.semilogx(period[pxy],self.rplst[ii]['phasexy'][0][pxy],
                             ls=':',marker='s',ms=4,color='k',mfc='k')
                axptm.semilogx(period[pyx],self.rplst[ii]['phaseyx'][0][pyx],
                             ls=':',marker='o',ms=4,color='k',mfc='k')
                             
            mpxy=[np.where(self.rplst[ii]['phasexy'][2]!=0)[0]]
            mpyx=[np.where(self.rplst[ii]['phaseyx'][2]!=0)[0]]
            axpte.semilogx(period[mpxy],self.rplst[ii]['phasexy'][2][mpxy],
                         ls='-',color=colorlst[jj])
            axptm.semilogx(period[mpyx],self.rplst[ii]['phaseyx'][2][mpyx],
                         ls='-',color=colorlst[jj])
                       
        axrte.grid(True,alpha=.4)
        axrtm.grid(True,alpha=.4)
        
        
        axrtm.set_xticklabels(['' for ii in range(10)])
        axrte.set_xticklabels(['' for ii in range(10)])
        
        rmstestr=np.median(np.array(rmstestr)[1:])
        rmstmstr=np.median(np.array(rmstmstr)[1:])
        axrte.set_title('TE rms={0:.2f}'.format(rmstestr),
                        fontdict={'size':10,'weight':'bold'})
        axrtm.set_title('TM rms={0:.2f}'.format(rmstmstr),
                        fontdict={'size':10,'weight':'bold'})
        
        axpte.grid(True,alpha=.4)
        axpte.yaxis.set_major_locator(MultipleLocator(10))
        axpte.yaxis.set_minor_locator(MultipleLocator(1))
        
        axrte.set_ylabel('App. Res. ($\Omega \cdot m$)',
                       fontdict={'size':10,'weight':'bold'})
        axpte.set_ylabel('Phase (deg)',
                       fontdict={'size':10,'weight':'bold'})
        axpte.set_xlabel('Period (s)',fontdict={'size':10,'weight':'bold'})
    
        axrte.yaxis.set_label_coords(-.08,.5)
        axpte.yaxis.set_label_coords(-.08,.5)
        
        axrtm.set_xticklabels(['' for ii in range(10)])
        axptm.grid(True,alpha=.4)
        axptm.yaxis.set_major_locator(MultipleLocator(10))
        axptm.yaxis.set_minor_locator(MultipleLocator(1))
        
        axrtm.set_ylabel('App. Res. ($\Omega \cdot m$)',
                       fontdict={'size':12,'weight':'bold'})
        axptm.set_ylabel('Phase (deg)',
                       fontdict={'size':12,'weight':'bold'})
        axptm.set_xlabel('Period (s)',fontdict={'size':12,'weight':'bold'})
    
        axrtm.yaxis.set_label_coords(-.08,.5)
        axptm.yaxis.set_label_coords(-.08,.5)
        plt.suptitle(station,fontsize=12,fontweight='bold')
        plt.show()
                                       
class Occam2DModel(Occam2DData):
    """
    This class deals with the model side of Occam inversions, including 
    plotting the model, the L-curve, depth profiles.  It will also be able to 
    build a mesh and regularization grid at some point.  
    
    It inherits Occam2DData and the data can be extracted from the method
    get2DData().  After this call you can use all the methods of Occam2DData,
    such as plotting the model responses and pseudo sections.
    
    
    """
    
    def __init__(self,iterfn,meshfn=None,inmodelfn=None):
        self.iterfn=iterfn
    
        self.invpath=os.path.dirname(self.iterfn)
        
        #get meshfile if none is provides assuming the mesh file is named
        #with mesh
        if self.invpath!=None:
            self.meshfn=os.path.join(self.invpath,'MESH')
            if os.path.isfile(self.meshfn)==False:
                for ff in os.listdir(self.invpath):
                    if ff.lower().find('mesh')>=0:
                        self.meshfn=os.path.join(self.invpath,ff)
                if os.path.isfile(self.meshfn)==False:
                    raise NameError('Could not find a mesh file, '+\
                                    'input manually')
            
        #get inmodelfile if none is provides assuming the mesh file is 
        #named with inmodel
        if inmodelfn==None:
            self.inmodelfn=os.path.join(self.invpath,'INMODEL')
            if os.path.isfile(self.inmodelfn)==False:
                for ff in os.listdir(self.invpath):
                    if ff.lower().find('inmodel')>=0:
                        self.inmodelfn=os.path.join(self.invpath,ff)
                if os.path.isfile(self.inmodelfn)==False:
                    raise NameError('Could not find a model file, '+\
                                    'input manually')
        
    def read2DIter(self):
        """
        read2DIter will read an iteration file and combine that info from the 
        datafn and return a dictionary of variables.
        
        Inputs:
            iterfn = full path to iteration file if iterpath=None.  If 
                           iterpath is input then iterfn is just the name
                           of the file without the full path.
        
        Outputs:
            idict = dictionary of parameters, keys are verbatim from the file, 
                    except for the key 'model' which is the contains the model
                    numbers in a 1D array.
            
        """
    
        #check to see if the file exists
        if os.path.exists(self.iterfn)==False:
            raise IOError('File: '+self.iterfn+' does not exist, check path')
    
        #open file, read lines, close file
        ifid=file(self.iterfn,'r')
        ilines=ifid.readlines()
        ifid.close()
        
        #create dictionary to put things
        self.idict={}
        ii=0
        #put header info into dictionary with similar keys
        while ilines[ii].find('Param')!=0:
            iline=ilines[ii].strip().split(':')
            self.idict[iline[0]]=iline[1].strip()
            ii+=1
        
        #get number of parameters
        iline=ilines[ii].strip().split(':')
        nparam=int(iline[1].strip())
        self.idict[iline[0]]=nparam
        self.idict['model']=np.zeros(nparam)
        kk=int(ii+1)
        
        jj=0
        while jj<len(ilines)-kk:
            iline=ilines[jj+kk].strip().split()
            for ll in range(4):
                try:
                    self.idict['model'][jj*4+ll]=float(iline[ll])
                except IndexError:
                    pass
            jj+=1
        
        #get the data file name from the iteration header
        self.datafn=self.idict['Data File']
        if self.datafn.find(os.sep)==-1:
            self.datafn=os.path.join(self.invpath,self.datafn)
        if os.path.isfile(self.datafn)==False:
            for ff in os.listdir(self.invpath):
                if ff.lower().find('.dat')>=0:
                    self.datafn=os.path.join(self.invpath,ff)
            if os.path.isfile(self.datafn)==False:
                raise NameError('Could not find a data file, input manually')
    
    def read2DInmodel(self):
        """
        read an INMODEL file for occam 2D
        
        Input:
            inmodelfn = full path to INMODEL file
        
        Output:
            rows = list of combined data blocks where first number of each list
                    represents the number of combined mesh layers for this 
                    regularization block.  The second number is the number of 
                    columns in the regularization block layer
            cols = list of combined mesh columns for the regularization layer.
                   The sum of this list must be equal to the number of mesh
                   columns.
            headerdict = dictionary of all the header information including the
                         binding offset
        """
        
        ifid=open(self.inmodelfn,'r')
        
        headerdict={}
        rows=[]
        cols=[]    
        ncols=[]
        
        ilines=ifid.readlines()
        
        for ii,iline in enumerate(ilines):
            if iline.find(':')>0:
                iline=iline.strip().split(':')
                headerdict[iline[0]]=iline[1]
                #append the last line
                if iline[0].find('EXCEPTIONS')>0:
                    cols.append(ncols)
            else:
                iline=iline.strip().split()
                iline=[int(jj) for jj in iline]
                if len(iline)==2:
                    if len(ncols)>0:
                        cols.append(ncols)
                    rows.append(iline)
                    ncols=[]
                elif len(iline)>2:
                    ncols=ncols+iline
                    
        self.rows=np.array(rows)
        self.cols=cols
        self.inmodel_headerdict=headerdict
        
    def read2DMesh(self):
        """
        read a 2D meshfn
        
        Input:
            meshfn = full path to mesh file
    
        Output:
            hnodes = array of horizontal nodes (column locations (m))
            vnodes = array of vertical nodes (row locations(m))
            mdata = free parameters
            
        Things to do:
            incorporate fixed values
        """
        
        mfid=file(self.meshfn,'r')
        
        mlines=mfid.readlines()
        
        nh=int(mlines[1].strip().split()[1])-1
        nv=int(mlines[1].strip().split()[2])-1
        
        hnodes=np.zeros(nh)
        vnodes=np.zeros(nv)
        mdata=np.zeros((nh,nv,4),dtype=str)    
        
        #get horizontal nodes
        jj=2
        ii=0
        while ii<nh:
            hline=mlines[jj].strip().split()
            for mm in hline:
                hnodes[ii]=float(mm)
                ii+=1
            jj+=1
        
        #get vertical nodes
        ii=0
        while ii<nv:
            vline=mlines[jj].strip().split()
            for mm in vline:
                vnodes[ii]=float(mm)
                ii+=1
            jj+=1    
        
        #get free parameters        
        for ii,mm in enumerate(mlines[jj+1:]):
            kk=0
            while kk<4:        
                mline=mm.rstrip()
                if mline.find('EXCEPTION')>0:
                    break
                for jj in range(nh):
                    try:
                        mdata[jj,ii,kk]=mline[jj]
                    except IndexError:
                        pass
                kk+=1
        
        #make the node information an attributes of the occamModel class 
        self.hnodes=hnodes
        self.vnodes=vnodes
        self.meshdata=mdata
        
    def get2DData(self):
        try:
            self.read2DdataFile()
        except AttributeError:
            print 'No Data file defined'
        
    def get2DModel(self):
        """
        get2DModel will create an array based on the FE mesh and fill the 
        values found from the regularization grid.  This way the array can 
        be manipulated as a 2D object and plotted as an image or a mesh.
        
        Outputs:
            self.2Dmodel -> model array with log resistivity values
            self.plotx -> horizontal distance of FE mesh (m) blocks
            self.ploty -> depth of vertical nodes of FE mesh (m)
        """
        
        #read iteration file to get model and data file
        self.read2DIter() 
        
        #read in data file as an OccamData type
        print 'Reading data from: ',self.datafn
        self.get2DData()
        
        #read in MESH file
        print 'Reading mesh from: ',self.meshfn
        self.read2DMesh()
        
        #read in INMODEL
        print 'Reading model from: ',self.inmodelfn
        self.read2DInmodel()
        #get the binding offset which is the right side of the furthest left
        #block, this helps locate the model in relative space
        bndgoff=float(self.inmodel_headerdict['BINDING OFFSET'])
        
        #make sure that the number of rows and number of columns are the same
        assert len(self.rows)==len(self.cols)
        
        #initiate the resistivity model to the shape of the FE mesh
        resmodel=np.zeros((self.vnodes.shape[0],self.hnodes.shape[0]))
        
        #read in the model and set the regularization block values to map onto
        #the FE mesh so that the model can be plotted as an image or regular 
        #mesh.
        mm=0
        for ii in range(len(self.rows)):
            #get the number of layers to combine
            #this index will be the first index in the vertical direction
            ny1=self.rows[:ii,0].sum()
            #the second index  in the vertical direction
            ny2=ny1+self.rows[ii][0]
            #make the list of amalgamated columns an array for ease
            lc=np.array(self.cols[ii])
            #loop over the number of amalgamated blocks
            for jj in range(len(self.cols[ii])):
                #get first in index in the horizontal direction
                nx1=lc[:jj].sum()
                #get second index in horizontal direction
                nx2=nx1+lc[jj]
                #put the apporpriate resistivity value into all the amalgamated 
                #model blocks of the regularization grid into the forward model
                #grid
                resmodel[ny1:ny2,nx1:nx2]=self.idict['model'][mm]
                mm+=1
        
        #make some arrays for plotting the model
        plotx=np.array([self.hnodes[:ii+1].sum() 
                        for ii in range(len(self.hnodes))])
        ploty=np.array([self.vnodes[:ii+1].sum() 
                        for ii in range(len(self.vnodes))])
        
        #center the grid onto the station coordinates
        x0=bndgoff-plotx[self.cols[0][0]]
        plotx=plotx+x0
        
        #flip the arrays around for plotting purposes
        #plotx=plotx[::-1] and make the first layer start at zero
        ploty=ploty[::-1]-ploty[0]
        
        #make a mesh grid to plot in the model coordinates
        self.meshx,self.meshy=np.meshgrid(plotx,ploty)
        
        #flip the resmodel upside down so that the top is the stations
        resmodel=np.flipud(resmodel)
        
        #make attributes of the class
        self.resmodel=resmodel
        self.plotx=plotx
        self.ploty=ploty
        
        #set the offsets of the stations and station list.
        self.offsetlst=[]
        for rpdict in self.rplst:
            self.offsetlst.append(rpdict['offset'])
        
    def plot2DModel(self,datafn=None,
                    xpad=1.0,ypad=1.0,mpad=0.5,spad=1.0,ms=60,stationid=None,
                    fdict={'size':8,'rotation':60,'weight':'normal'},
                    dpi=300,ylimits=None,xminorticks=5,yminorticks=1,
                    climits=(0,4), cmap='jet_r',fs=8,femesh='off',
                    regmesh='off',aspect='auto',title='on',meshnum='off',
                    blocknum='off',blkfdict={'size':3},fignum=1,
                    plotdimensions=(10,10),grid='off',yscale='km'):
        """
        plotModel will plot the model output by occam in the iteration file.
        
        Inputs:
            
            datafn = full path to data file.  If none is input it will use the
                        data file found in the iteration file.
            
            xpad = padding in the horizontal direction of model
            
            ypad = padding the in the vertical direction of the top of the model
                   to fit the station names and markers
                   
            mpad = marker pad to fit right at the surface, haven't found a better
                   way of doing this automatically yet
                   
            spad = padding of station names away from the top of the model, this
                    is kind of awkward at the moment especially if you zoom into 
                    the model, it usually looks retarded and doesn't fit
                    
            ms = marker size in ambiguous points
            
            stationid = index of station names to plot -> ex. pb01sdr would be 
                        stationid=(0,4) to plot pb01
                        
            fdict = font dictionary for the station names, can have keys:
                    'size' = font size
                    'rotation' = angle of rotation (deg) of font
                    'weight' = weight of font 
                    'color' = color of font
                    'style' = style of font ex. 'italics'
                    
            plotdimensions = x-y dimensions of the figure (10,10) in inches
                    
            dpi = dot per inch of figure, should be 300 for publications
            
            ylimits = limits of depth scale (km). ex, ylimits=(0,30)
            
            xminorticks = location of minor tick marks for the horizontal axis
            
            yminorticks = location of minor tick marks for vertical axis
            
            climits = limits of log10(resistivity). ex. climits=(0,4)
            
            cmap = color map to plot the model image
            
            fs = font size of axis labels
            
            femesh = 'on' to plot finite element forward modeling mesh (black)
            
            regmesh = 'on' to plot regularization mesh (blue)
            
            aspect = aspect ratio of the figure, depends on your line length and
                    the depth you want to investigate
            
            title = 'on' to put the RMS and Roughness as the title, or input a 
                    string that will be added to the RMS and roughness, or put 
                    None to not put a title on the plot and print out RMS and 
                    roughness
            
            meshnum = 'on' to plot FE mesh block numbers
            
            fignum = figure number to plot to
            
            blocknum = 'on' to plot numbers on the regularization blocks
            
            blkfdict = font dictionary for the numbering of regularization blocks
            
            grid = major for major ticks grid
                   minor for a grid of the minor ticks
                   both for a grid with major and minor ticks
            
            yscale = 'km' for depth in km or 'm' for depth in meters
        """   
                    
        #set the scale of the plot
        if yscale=='km':
            dfactor=1000.
            pfactor=1.0
        elif yscale=='m':
            dfactor=1.
            pfactor=1000.
        else:
            dfactor=1000.
            pfactor=1.0
        
        #get the model
        self.get2DModel()
        
        #set some figure properties to use the maiximum space 
        plt.rcParams['font.size']=int(dpi/40.)
        plt.rcParams['figure.subplot.left']=.08
        plt.rcParams['figure.subplot.right']=.99
        plt.rcParams['figure.subplot.bottom']=.1
        plt.rcParams['figure.subplot.top']=.92
        plt.rcParams['figure.subplot.wspace']=.01
#        plt.rcParams['text.usetex']=True
        
        #plot the model as a mesh
        fig=plt.figure(fignum,plotdimensions,dpi=dpi)
        plt.clf()
        
        #add a subplot to the figure with the specified aspect ratio
        ax=fig.add_subplot(1,1,1,aspect=aspect)
        
        #plot the model as a pcolormesh so the extents are constrained to 
        #the model coordinates
        ax.pcolormesh(self.meshx/dfactor,self.meshy/dfactor,self.resmodel,
                      cmap=cmap,vmin=climits[0],vmax=climits[1])
        
        #make a colorbar for the resistivity
        cbx=make_axes(ax,shrink=.8,pad=.01)
        cb=ColorbarBase(cbx[0],cmap=cmap,norm=Normalize(vmin=climits[0],
                        vmax=climits[1]))
        cb.set_label('Resistivity ($\Omega \cdot$m)',
                     fontdict={'size':fs,'weight':'bold'})
        cb.set_ticks(np.arange(int(climits[0]),int(climits[1])+1))
        cb.set_ticklabels(['10$^{0}$'.format(nn) for nn in 
                            np.arange(int(climits[0]),int(climits[1])+1)])
        
        #set the offsets of the stations and plot the stations
        #need to figure out a way to set the marker at the surface in all
        #views.
        for rpdict in self.rplst:
            #plot the station marker
            #plots a V for the station cause when you use scatter the spacing
            #is variable if you change the limits of the y axis, this way it
            #always plots at the surface.
            ax.text(rpdict['offset']/dfactor,self.ploty.min(),'V',
                    horizontalalignment='center',
                    verticalalignment='baseline',
                    fontdict={'size':ms,'weight':'bold','color':'black'})
                    
            #put station id onto station marker
            #if there is a station id index
            if stationid!=None:
                ax.text(rpdict['offset']/dfactor,-spad*pfactor,
                        rpdict['station'][stationid[0]:stationid[1]],
                        horizontalalignment='center',
                        verticalalignment='baseline',
                        fontdict=fdict)
            #otherwise put on the full station name found form data file
            else:
                ax.text(rpdict['offset']/dfactor,-spad*pfactor,
                        rpdict['station'],
                        horizontalalignment='center',
                        verticalalignment='baseline',
                        fontdict=fdict)
        
        #set the initial limits of the plot to be square about the profile line  
        if ylimits==None:  
            ax.set_ylim(abs(max(self.offsetlst)-min(self.offsetlst))/dfactor,
                        -ypad*pfactor)
        else:
            ax.set_ylim(ylimits[1]*pfactor,(ylimits[0]-ypad)*pfactor)
        ax.set_xlim(min(self.offsetlst)/dfactor-(xpad*pfactor),
                     (max(self.offsetlst)/dfactor+(xpad*pfactor)))
        #set the axis properties
        ax.xaxis.set_minor_locator(MultipleLocator(xminorticks*pfactor))
        ax.yaxis.set_minor_locator(MultipleLocator(yminorticks*pfactor))
        if yscale=='km':
            ax.set_xlabel('Horizontal Distance (km)',
                          fontdict={'size':fs,'weight':'bold'})
            ax.set_ylabel('Depth (km)',fontdict={'size':fs,'weight':'bold'})
        elif yscale=='m':
            ax.set_xlabel('Horizontal Distance (m)',
                          fontdict={'size':fs,'weight':'bold'})
            ax.set_ylabel('Depth (m)',fontdict={'size':fs,'weight':'bold'})
        
        #put a grid on if one is desired    
        if grid=='major':
            ax.grid(alpha=.3,which='major')
        if grid=='minor':
            ax.grid(alpha=.3,which='minor')
        if grid=='both':
            ax.grid(alpha=.3,which='both')
        else:
            pass
        
        #set title as rms and roughness
        if type(title) is str:
            if title=='on':
                titlestr=os.path.join(os.path.basename(os.path.dirname(self.iterfn)),
                                      os.path.basename(self.iterfn))
                ax.set_title(titlestr+\
                            ': RMS {0:.2f}, Roughness={1:.0f}'.format(
                            float(self.idict['Misfit Value']),
                            float(self.idict['Roughness Value'])),
                            fontdict={'size':fs+1,'weight':'bold'})
            else:
                ax.set_title(title+'; RMS {0:.2f}, Roughness={1:.0f}'.format(
                         float(self.idict['Misfit Value']),
                         float(self.idict['Roughness Value'])),
                         fontdict={'size':fs+1,'weight':'bold'})
        else:
            print 'RMS {0:.2f}, Roughness={1:.0f}'.format(
                         float(self.idict['Misfit Value']),
                         float(self.idict['Roughness Value'])) 
        
        #plot forward model mesh    
        if femesh=='on':
            for xx in self.plotx/dfactor:
                ax.plot([xx,xx],[0,self.ploty[0]/dfactor],color='k',lw=.5)
            for yy in self.ploty/dfactor:
                ax.plot([self.plotx[0]/dfactor,self.plotx[-1]/dfactor],
                        [yy,yy],color='k',lw=.5)
        
        #plot the regularization mesh
        if regmesh=='on':
            linelst=[]
            for ii in range(len(self.rows)):
                #get the number of layers to combine
                #this index will be the first index in the vertical direction
                ny1=self.rows[:ii,0].sum()
                #the second index  in the vertical direction
                ny2=ny1+self.rows[ii][0]
                #make the list of amalgamated columns an array for ease
                lc=np.array(self.cols[ii])
                yline=ax.plot([self.plotx[0]/dfactor,self.plotx[-1]/dfactor],
                              [self.ploty[-ny1]/dfactor,
                               self.ploty[-ny1]/dfactor],
                              color='b',lw=.5)
                linelst.append(yline)
                #loop over the number of amalgamated blocks
                for jj in range(len(self.cols[ii])):
                    #get first in index in the horizontal direction
                    nx1=lc[:jj].sum()
                    #get second index in horizontal direction
                    nx2=nx1+lc[jj]
                    try:
                        if ny1==0:
                            ny1=1
                        xline=ax.plot([self.plotx[nx1]/dfactor,
                                       self.plotx[nx1]/dfactor],
                                      [self.ploty[-ny1]/dfactor,
                                       self.ploty[-ny2]/dfactor],
                                      color='b',lw=.5)
                        linelst.append(xline)
                    except IndexError:
                        pass
                    
        ##plot the mesh block numbers
        if meshnum=='on':
            kk=1
            for yy in self.ploty[::-1]/dfactor:
                for xx in self.plotx/dfactor:
                    ax.text(xx,yy,'{0}'.format(kk),fontdict={'size':3})
                    kk+=1
                    
        ##plot regularization block numbers
        if blocknum=='on':
            kk=1
            for ii in range(len(self.rows)):
                #get the number of layers to combine
                #this index will be the first index in the vertical direction
                ny1=self.rows[:ii,0].sum()
                #the second index  in the vertical direction
                ny2=ny1+self.rows[ii][0]
                #make the list of amalgamated columns an array for ease
                lc=np.array(self.cols[ii])
                #loop over the number of amalgamated blocks
                for jj in range(len(self.cols[ii])):
                    #get first in index in the horizontal direction
                    nx1=lc[:jj].sum()
                    #get second index in horizontal direction
                    nx2=nx1+lc[jj]
                    try:
                        if ny1==0:
                            ny1=1
                        #get center points of the blocks
                        yy=self.ploty[-ny1]-(self.ploty[-ny1]-
                                                self.ploty[-ny2])/2
                        xx=self.plotx[nx1]-(self.plotx[nx1]-self.plotx[nx2])/2
                        #put the number
                        ax.text(xx/dfactor,yy/dfactor,'{0}'.format(kk),
                                fontdict=blkfdict,
                                horizontalalignment='center',
                                verticalalignment='center')
                        kk+=1
                    except IndexError:
                        pass
                    
        plt.show()
    
    def plotL2Curve(self,fnstem=None,fignum=1,dpi=300):
        """
        PlotL2Curve will plot the RMS vs iteration number for the given 
        inversion folder and roughness vs iteration number
        
        Inputs: 
            fnstem = filename stem to look for in case multiple inversions were
                    run in the same folder.  If none then searches for anything
                    ending in .iter
            fignum = figure number
            dpi = dpi of the figure
        
        """ 

        invpath=os.path.dirname(self.iterfn)        
        
        if fnstem==None:
            iterlst=[os.path.join(invpath,itfile) 
                    for itfile in os.listdir(invpath) if itfile.find('.iter')>0]
        else:
            iterlst=[os.path.join(invpath,itfile) 
                    for itfile in os.listdir(invpath) if itfile.find('.iter')>0 and
                    itfile.find(fnstem)>0]
                    
        nr=len(iterlst)
        
        rmsarr=np.zeros((nr,2))
        
        for itfile in iterlst:
            self.iterfn=itfile
            self.read2DIter()
            ii=int(self.idict['Iteration'])
            rmsarr[ii,0]=float(self.idict['Misfit Value'])
            rmsarr[ii,1]=float(self.idict['Roughness Value'])
        
        #set the dimesions of the figure
        plt.rcParams['font.size']=int(dpi/40.)
        plt.rcParams['figure.subplot.left']=.08
        plt.rcParams['figure.subplot.right']=.90
        plt.rcParams['figure.subplot.bottom']=.1
        plt.rcParams['figure.subplot.top']=.90
        plt.rcParams['figure.subplot.wspace']=.01
        
        #make figure instance
        fig=plt.figure(fignum,[6,5],dpi=dpi)
        plt.clf()
        
        #make a subplot for RMS vs Iteration
        ax1=fig.add_subplot(1,1,1)
        
        #plot the rms vs iteration
        l1,=ax1.plot(np.arange(1,nr,1),rmsarr[1:,0],'-k',lw=1,marker='d',ms=5)
        
        #plot the median of the RMS
        m1,=ax1.plot(np.arange(0,nr,1),np.repeat(np.median(rmsarr[1:,0]),nr),
                     '--r',lw=.75)
        
        #plot the mean of the RMS
        m2,=ax1.plot(np.arange(0,nr,1),np.repeat(np.mean(rmsarr[1:,0]),nr),
                     ls='--',color='orange',lw=.75)
    
        #make subplot for RMS vs Roughness Plot
        ax2=ax1.twiny()
        
        #plot the rms vs roughness 
        l2,=ax2.plot(rmsarr[1:,1],rmsarr[1:,0],'--b',lw=.75,marker='o',ms=7,
                     mfc='white')
        for ii,rms in enumerate(rmsarr[1:,0],1):
            ax2.text(rmsarr[ii,1],rms,'{0}'.format(ii),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontdict={'size':6,'weight':'bold','color':'blue'})
        
        #make a legend
        ax1.legend([l1,l2,m1,m2],['RMS','Roughness',
                   'Median_RMS={0:.2f}'.format(np.median(rmsarr[1:,0])),
                    'Mean_RMS={0:.2f}'.format(np.mean(rmsarr[1:,0]))],
                    ncol=4,loc='upper center',columnspacing=.25,markerscale=.75,
                    handletextpad=.15)
                    
        #set the axis properties for RMS vs iteration
        ax1.yaxis.set_minor_locator(MultipleLocator(.1))
        ax1.xaxis.set_minor_locator(MultipleLocator(1))
        ax1.set_ylabel('RMS',fontdict={'size':8,'weight':'bold'})                                   
        ax1.set_xlabel('Iteration',fontdict={'size':8,'weight':'bold'})
        ax1.grid(alpha=.25,which='both')
        ax2.set_xlabel('Roughness',fontdict={'size':8,'weight':'bold',
                                             'color':'blue'})
        for t2 in ax2.get_xticklabels():
            t2.set_color('blue')          
        
        plt.show()
                
    def plotDepthModel(self,dpi=300,depth=10000,plottype='1',yscale='log',
                       plotdimensions=(3,6),plotnum=1,fignum=1):
        """
        will plot a depth section profile for a given set of stations.
        
        Inputs:
            
            plotnum = 1 to plot in different figures, 'all' to plot in all into
                      one figure.
            
            dpi = dpi of figure
            
            depth = max depth to estimate the profile
            
            stationnames = list of station names corresponding to the starting
                           block numbers
            
            yscale = 'log' for logarithmic or 'linear' for linear
            
        """

        try:
            self.offsetlst
        except AttributeError:
            self.get2DModel()
        #get stations to plot
        if plottype=='1':
            pstationlst=np.arange(len(self.data.stationlst))
        else:
            pstationlst=[]
            if type(plottype) is not list:
                plottype=[plottype]
            for ps in plottype:
                for ii,ss in enumerate(self.data.stationlst):
                    if ss.find(ps)==0:
                        pstationlst.append(ii)
                                  
        #get the average x-spacing within the station region, occam pads by 
        #7 cells by default        
        xavg=np.floor(np.mean([abs(self.plotx[ii]-self.plotx[ii+1]) 
                        for ii in range(7,len(self.plotx)-7)]))
        
        #get the station indices to extract from the model
        slst=[]
        for ff in pstationlst:
            offset=self.offsetlst[ff]
            for ii,xx in enumerate(self.plotx):
                if offset>=xx-xavg/2. and offset<=xx+xavg/2.:
                    slst.append(ii)
        
        #set the dimesions of the figure
        plt.rcParams['font.size']=int(dpi/40.)
        plt.rcParams['figure.subplot.left']=.15
        plt.rcParams['figure.subplot.right']=.95
        plt.rcParams['figure.subplot.bottom']=.15
        plt.rcParams['figure.subplot.top']=.90
        plt.rcParams['figure.subplot.wspace']=.05
        
        if plotnum=='all':
            #set the dimesions of the figure
            plt.rcParams['font.size']=int(dpi/60.)
            plt.rcParams['figure.subplot.left']=.09
            plt.rcParams['figure.subplot.right']=.95
            plt.rcParams['figure.subplot.bottom']=.15
            plt.rcParams['figure.subplot.top']=.90
            plt.rcParams['figure.subplot.wspace']=.1
            
            fig=plt.figure(fignum,plotdimensions,dpi=dpi)
            plt.clf()
            ns=len(slst)
            #plot the depth section for each station        
            for ii,ss in enumerate(slst):
                ax=fig.add_subplot(1,ns,ii+1)
                
                #plot resistivity vs depth
                if yscale=='linear':
                    p1,=ax.semilogx(10**self.resmodel[:,ss],self.ploty,
                                    ls='steps-')
                elif yscale=='log':
                    if self.ploty[-1]==0.0:
                        self.ploty[-1]=1
                    p1,=ax.loglog(10**self.resmodel[:,ss],self.ploty,
                                  ls='steps-')
                    ax.set_ylim(depth,self.ploty[-1])
                
                ax.set_title(self.data.stationlst[pstationlst[ii]],
                             fontdict={'size':10,'weight':'bold'})
                if ii==0:
                    ax.set_ylabel('Depth (m)',
                                  fontdict={'size':8,'weight':'bold'})
                else:
                    plt.setp(ax.yaxis.get_ticklabels(),visible=False)
                if ii==np.round(ns/2.):
                    ax.set_xlabel('Resistivity ($\Omega \cdot$m)',
                                  fontdict={'size':8,'weight':'bold'})
                ax.grid(True,alpha=.3,which='both')
                ax.set_xlim(10**self.resmodel.min(),10**self.resmodel.max())
        else:
            #plot the depth section for each station        
            for ii,ss in enumerate(slst):
                fig=plt.figure(ii+1,plotdimensions,dpi=dpi)
                plt.clf()
                ax=fig.add_subplot(1,1,1)
                
                #plot resistivity vs depth
                if yscale=='linear':
                    p1,=ax.semilogx(10**self.resmodel[:,ss],self.ploty,
                                    ls='steps-')
                elif yscale=='log':
                    if self.ploty[-1]==0.0:
                        self.ploty[-1]=1
                    p1,=ax.loglog(10**self.resmodel[:,ss],self.ploty,
                                  ls='steps-')
                ax.set_ylim(depth,self.ploty[-1])
                
                ax.set_title(self.data.stationlst[pstationlst[ii]],
                             fontdict={'size':10,'weight':'bold'})    
                ax.set_ylabel('Depth (m)',fontdict={'size':8,'weight':'bold'})
                ax.set_xlabel('Resistivity ($\Omega \cdot$m)',
                              fontdict={'size':8,'weight':'bold'})
                ax.grid(True,alpha=.3,which='both')       
            
        
    