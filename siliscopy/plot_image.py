#    Copyright 2020,2021 SUBHAMOY MAHAJAN 
#    
#    This file is part of InSilicoMicroscopy software.
# 
#    InSilicoMicroscopy is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.)

# Creates a colored in-silico microscopy image from in-silico monochrome image 
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
import copy
import tifffile as tif
small=1E-10

def get_grey_img(filename, I0, lam, T, ti, fs, MaxBox, frame=False, \
    opt_axis=None, nidx=None, frame_col=1.0, noise=False, poi=None, 
    gauss=None, psf_type=0, tsO=None):
    """ Calculates greyscale image
     
    Parameters
    ----------
    filename: str
        Filename header for image data file
    I0: float
        The maximum image intensity 
    lam: int
        The wavelength
    T: int
        Number of timesteps to perform an average.
    ti: int
        timestep of the image data file. -1 if there is no sense of time
        (static system).
    fs: int
        Scaling factor for wave vector or MS position coordinates.
    MaxBox: array of ints
        Contains the number of pixels in the image in l and m directions.
    frame: Bool, optional
        True keeps the image intensity of white frame as -1. False converts
        the image intensities of -1 to frame_col. (default is False).
    opt_axis: int, optional
        Optical axis 0, 1, and 2 for x, y, and z axis. (default is None)
    nidx: int, optional    
        index of n' axis. (default is None)
    noise: Bool
        If true, noise is added the to image intensities. (default is False)
    poi: float
        Effectiveness of poison noise. Takes value between 0 and 1. 0 is no 
        noise whereas 1 is full poisson noise based on ```Lanza, A.; Morigi,
        S.; Sgallari, F.; Wen, Y. W. Image Restoration with Poisson-Gaussian 
        Mixed Noise. Comput. Methods Biomech. Biomed. Eng. Imaging Vis. 
        2014, 2 (1), 12–24.)```. (default None)
    gauss: float
        Variance of the 0-mean Gaussian noise. (default None)
    psf_type: int
        0 is depth-invariant PSF with circular symmetry. 1 is depth-variant 
        PSF with circular symmetry. Other options might be added in the 
        future (default 0)
    tsO: float
        Distance between the bottom of the coverslip and the object focal 
        plane in nm. Only relevant for depth-variant PSF. (default None)

    Returns
    -------
    IMG: 2D ndarray
        Image intensities between 0 and 1. Image intensity of -1 implies white 
        frame (absence of molecular simulation system). Axes are XY or LM.
    """
    if ti<0 and T>1:
        raise Exception('More than one timesteps cannot be used for a' + \
            ' simulation without time.')
    IMG=np.zeros((MaxBox[0],MaxBox[1]))
    Cnt=np.zeros((MaxBox[0],MaxBox[1]),dtype=int)
    nstr=''
    if nidx != None:
        xyz='xyz'
        nstr='_'+xyz[opt_axis]+str(nidx)
    tstr=''
    if psf_type==1:
        tstr='_tsO'+"%g"%tsO
    for i in range(T):
        if ti>=0:
            fname=filename + str(i+ti) + nstr + tstr + '_lam' + str(lam) + \
                '_fs' + str(fs) + '.dat'
        else:
            fname=filename + nstr + tstr + '_lam' + str(lam) + '_fs' + \
                str(fs) + '.dat'
        print('Reading: '+fname+'      ',end='\r') 
        f=open(fname,'r')
        j=0
        for lines in f:
            foo=lines.split()
            if foo[0][0]=='#':
                continue
            for k in range(len(IMG[0])):
                I=float(foo[k])*I0
                if I>1:
                    IMG[j,k]+=1.0
                    Cnt[j,k]+=1
                elif I>= -small:
                    IMG[j,k]+=I
                    Cnt[j,k]+=1
                # else its white frame - do nothing
            j+=1                            
        f.close()
    for j in range(len(IMG)):
        for k in range(len(IMG[0])):
            if Cnt[j,k]>0:
                IMG[j,k]=IMG[j,k]/float(Cnt[j,k])
            else:
                if frame:
                    IMG[j,k]=-1
                else:
                    IMG[j,k]=frame_col
    if noise:
        IMG=add_noise(IMG,poi,gauss) 
    return IMG

def add_scale(IMG, scale, Bm):
    """ Adds a scale bar to the in-silico image
       
    Parameters
    ----------
    IMG: ndarray
        Image intensities. Axes are XY or LM.
    scale: float
        Size of scale bar in nm.
    Bm:
        Size of maximum box length in m direction
 
    Returns
    -------
    IMG: ndarray
        Image intensities with a scale bar.
    """
    L=int(scale/Bm*len(IMG[0]))
    Llast=int(0.9*len(IMG[0]))
    Hlast=int(0.9*len(IMG))
    wid=int(len(IMG)*0.005)
    for i in range(Llast-L,Llast+1):
        for j in range(Hlast-wid,Hlast+wid+1):
            IMG[j][i]=1.0
    return IMG

def plot_ism(IMG, lam_I0, lam, T, ti, fs, img_hei=3.0, filename=None, 
    show=False, gcolmap='gray', dpi=600, otype='jpeg', psf_type=0, tsO=None,
    frame_col=1.0, dlmn=None, pbc=None):
    """ Plots in-silico microscopy image.
    
    Parameters
    ----------
    IMG: 
        see ''add_scale''. Should be in XYC or XY format  
    lam_I0: array of float #change to lam_I0s
        An array containing maximum intensities of fluorophores
    lam: array of integers #change to lams
        An array of wavelength of fluorophores
    T: 
        see ''get_grey_img''
    ti: 
        see ''get_grey_img''
    fs: 
        see ''get_grey_img''
    img_hei: float
        Physical image height in inches
    filename: str, optional
        Filename to save the image (default value is None)
    show: bool, optional
        Shows the image instead of saving if it is True. (default is False)
    gcolmap: string, optional
        Color map for monochrome image. (default is 'gray')
    dpi: int, optional
        Dots per square inch for the image if saved to a file.
    otype: str, optional
        Output type of image, 'jpeg','png' or 'tiff'. (default is 'jpeg')
    psf_type: 
        see ''get_grey_img''
    tsO: 
        see ''get_grey_img''
    frame_col:
        see ''get_grey_img''

    Writes
    ------
    [filename]: JPEG Image file
        Writes the in-silico microscopy image if show is False and filename 
        is not None
    """
    consts=IMG.shape
    if filename!=None:
        Istring=''
        for i in range(len(lam_I0)):
            Istring+='_'+str(round(lam_I0[i],4))
        tstr=''
        if psf_type==1:
            tstr='_tsO'+"%g"%tsO
        if ti>=0:#dynamic gro structure 
            if len(lam_I0)==1: #mono
                fname=filename+str(ti) +tstr +'_lam'+str(lam[0]) +'_fs'+ \
                      str(fs) + '_T' + str(T) + '_I' + str(lam_I0[0]) +'.'+otype
            else:#color
                fname=filename+str(ti) +tstr +'_fs'+str(fs) +'_T'+str(T) + \
                      '_I' + Istring +'.'+otype
        else:# static gro structure
            if len(lam_I0)==1:#mono
                fname=filename +tstr +'_lam'+str(lam[0]) +'_fs'+str(fs) +'_I'+ \
                      str(lam_I0[0]) +'.'+otype
            else:#color
                fname=filename +tstr +'_fs'+str(fs) +'_I'+Istring + '.'+otype

    if otype in ["jpeg", "png", "JPEG", "PNG"]:
        img_width=consts[1]*img_hei/consts[0]
        IMG[IMG<0]=frame_col
        fig,ax=plt.subplots(1, 1, figsize=(img_width, img_hei))
        if len(consts)==2: #Greyscale
            ax.imshow(IMG, vmin=0, vmax=1, cmap=gcolmap)
        else: #Color
            ax.imshow(IMG)

        ax.set_xticks([])
        ax.set_yticks([])
        plt.axis('off')
        plt.tight_layout(pad=0)
        if filename==None or show==True:
            plt.show()
            return
        print('Writing: '+fname)
        plt.savefig(fname,dpi=dpi)
        plt.close()
    else:
        foo=1
        if otype[:-2]=='tiff':
            foo=2
        if len(consts)==2: #Greyscale
            IMG,bounds=intensity2image(IMG,'uint'+otype.split('f')[-1],
                axes='XY')
            #IMG is in shape XY to ensure tiff is written as YX 
            tif.imwrite(fname[:-foo],IMG,photometric='minisblack',imagej=True,
                resolution=(1./dlmn[0],1./dlmn[1]), metadata={ 'unit':'nm', 
                'pbc': pbc, 'bounds':bounds, 'axes':'YX'})
        else: #Color
            IMG=np.transpose(IMG,(2,0,1)) #Now IMG is CXY
            IMG,bounds=intensity2image(IMG,'uint'+otype.split('f')[-1],
                axes='CXY') 
            tif.imwrite(fname[:-foo],IMG, imagej=True, 
                resolution=(1./dlmn[0],1./dlmn[1]), metadata={'unit': 'nm', 
                'pbc': pbc, 'bounds':bounds, 'axes':'CYX'})
        print('Writing: '+fname[:-foo])
    return

def get_col_img(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, 
    mix_type='mt', opt_axis=None, nidx=None, noise=False,  poi=None, 
    gauss=None, psf_type=0, tsO=None):
    """ Calculates the image intensity for a color image,

    Parameters
    ----------
    filename: str
        Filename header for image data file
    lam_I0s: array of floats
        The maximum image intensities of all fluorophore types
    lams: array of int
        The wavelength of all fluorophore types
    lam_hues: array of floats
        The hue in degree of all fluorophore types
    T: 
        see ''get_grey_img''
    ti: 
        see ''get_grey_img''
    fs: 
        see ''get_grey_img''
    MaxBox: 
        see ''get_grey_img''
    frame_col: 
        see ''get_grey_img''
    mix_type: str
        Algorithm to mix colors. 'mt' for Mahajan and Tang, 'rgb' for Red-
        Green-Blue. Addition is CMYK is not supported.
    poi:
        see ''get_grey_img''
    gauss:
        see ''get_grey_img''
    psf_type:
        see ''get_grey_img''
    tsO:
        see ''get_grey_img''

    Returns
    ------- 
    IMG: 3D ndarray
        Axes XYC. Axis 2 corresponds to red, green and blue channels. Image 
        intensities between 0 and 1.
    """
    IMGs=np.zeros((MaxBox[0],MaxBox[1],len(lams)))
    for i in range(len(lams)):
        foo=get_grey_img(filename, lam_I0s[i], lams[i], T, ti, fs, MaxBox, 
            frame=True, opt_axis=opt_axis, nidx=nidx, noise=noise, poi=poi, 
            gauss=gauss, psf_type=psf_type, tsO=tsO)
        IMGs[:,:,i]=foo[:,:]
    if mix_type=='none' or mix_type=='nomix':
        return IMGs
    col_IMG=add_color(IMGs,lam_hues, -1, mix_type)
    return col_IMG  

def hsv2rgb(h, s, v):
    """ Convert hue-saturation-value to red-green-blue

    Based on ```Smith, A. R. Color Gamut Transforma Pairs. ACM SIGGRAPH Comput.
    Graph. 1978, 12, 12–19```. Similar to colorsys module, but it does not 
    lose precision by converting them into 8-bit integers.

    Parameters
    ----------
    h: float
        Hue between 0 (0 degrees) and 1 (360 degrees).
    s: float
        Saturation between 0 and 1.
    v: float
        Value between 0 and 1.

    Returns
    -------
        red, green, blue between 0 and 1.
    """
    if h>1 or s>1 or v>1:
        raise Exception("h, s, or v > 1")

    A1=v #C+m
    A2=v*(1 - s*abs((h*6)%2-1))  #X+m
    A3=v*(1 - s) #m
    if h<1/6.:
        return A1,A2,A3
    elif h<2/6.:
        return A2,A1,A3
    elif h<3/6.:
        return A3,A1,A2
    elif h<4/6.:
        return A3,A2,A1
    elif h<5/6.:
        return A2,A3,A1
    else:
        return A1,A3,A2

def rgb2hsv(r, g, b):
    """ Convert red-green-blue to hue-saturation-value  

    Based on ```Smith, A. R. Color Gamut Transforma Pairs. ACM SIGGRAPH Comput.
    Graph. 1978, 12, 12–19```. Similar to colorsys module, but it does not 
    lose precision by converting them into 8-bit integers.

    Parameters
    ----------
    r: float
        Red between 0 and 1.
    g: float
        Green between 0 and 1.
    b: float
        Blue between 0 and 1.

    Returns
    -------
        hue, saturation, value between 0 and 1.
    """
    if r>1 or g>1 or b>1:
        raise Exception("r, g, or b > 1")

    Cmax=max(r,g,b)
    Cmin=min(r,g,b)
    delta=Cmax-Cmin
    if delta<1E-6:
        h=0
    elif Cmax==r: 
        h=(((g-b)/delta)%6)/6.
    elif Cmax==g:
        h=(((b-r)/delta)%6)/6.
    elif Cmax==b:
        h=(((r-g)/delta)%6)/6.

    if Cmax==0:
        s=0
    else:
        s=delta/Cmax
   
    return h,s, Cmax 

def add_color(IMGs, lam_hues, frame_col=1.0, mix_type='mt'):
    """ Calculates the image intensity for a color image,

    Parameters
    ----------
    IMGs:3D numpy array
        Monochrome image intensities. Axes XYC
    lam_hues:
        see ''get_col_img'' 
    frame_col:
        see ''get_grey_img''
    mix_type: str
        see ''get_col_img'' 

    Returns
    ------- 
    IMG: 3D ndarray
        Axes XYC. Axis 2 0,1,2 corresponds to red, green and blue channels. 
        Image intensities are floats between 0 and 1.
    """
    consts=IMGs.shape
    col_IMG=np.zeros((consts[0],consts[1],3))
    if mix_type=='rgb':
        cols=np.zeros((len(lam_hues),3))
        for lam_id in range(len(lam_hues)):
            rgb=hsv2rgb(lam_hues[lam_id]/360,1,1)
            cols[lam_id,:]=rgb[:]

    for i in range(consts[0]):
        for j in range(consts[1]):
            foo=0
            for lam_id in range(len(lam_hues)):
                if IMGs[i,j,lam_id]>-small:
                    foo=+1
            if foo==0:
                #if all Img_dat are -1 then res is -1
                col_IMG[i,j,:]=-1
            elif mix_type=='mt':
                xres=0
                yres=0
                Is=[]
                ncol=0
                for lam_id in range(len(lam_hues)):
                    if IMGs[i,j,lam_id]>small:
                        # V*e^(i(hue)) #I0 was multiplied when determining 
                        # grey images.
                        xres+=IMGs[i,j,lam_id]*np.cos(lam_hues[lam_id]* \
                                                       2*np.pi/360)   
                        yres+=IMGs[i,j,lam_id]*np.sin(lam_hues[lam_id]* \
                                                       2*np.pi/360)
                        Is.append(IMGs[i,j,lam_id])
                        ncol+=1

                if ncol==0: #No fluorescence; black background (by default)
                    continue
                Is=sorted(Is) 
                #arctan2 returns between [-pi,pi]. Dividing it by 2pi yields
                # [-0.5,0.5]
                hres=np.arctan2(yres,xres)/(2*np.pi)
                #this makes hres [0,1]
                if hres<0:
                    hres+=1
                vres=Is[-1] #Largest value
                if vres>1:
                    raise Exception("Color's Value is more than 1!")
                sres=1
                if ncol>2: #Color should be saturated
                    sres=1-Is[-3]/Is[-1]
                if sres<0 or sres>1:
                    raise Exception("Color's saturation is more than 1")

                rgb=hsv2rgb(hres,sres,vres)
                col_IMG[i,j,:]=rgb[:]
            elif mix_type=='rgb':
                rgb=np.zeros(3)
                for lam_id in range(len(lam_hues)):
                    rgb+=IMGs[i,j,lam_id]*cols[lam_id,:]
                for k in range(3):
                    if rgb[k]>1:
                        col_IMG[i,j,k]=1.0 
                    else:
                        col_IMG[i,j,k]=rgb[k]

    for i in range(consts[0]):
        for j in range(consts[1]):
            for k in range(3):
                if col_IMG[i,j,k]<-small:
                    col_IMG[i,j,k]=frame_col

    return col_IMG  

def add_noise(I,poi,gauss):
    """ Adds a Poisson-Gaussian noise to a monochrome image

    Parameters
    ----------
    I: 2D array (image)
        Monochrome image. Axes XY.
    poi: 
        see ''get_grey_img''
    gauss: 
        see ''get_grey_img''

    Returns
    -------
    I: Monochrome image with noise. Axes XY.
    """
    dims=I.shape
    x0,y0,xL,yL=[0,0,0,0]
    for i in range(dims[0]):
        if I[i,int(dims[1]/2)-1]==-1 and xL==0:
            x0+=1
        elif I[i,int(dims[1]/2)-1]>-0.5:
            xL+=1       
    for j in range(dims[1]):
        if I[int(dims[0]/2)-1,j]==-1 and yL==0:
            y0+=1
        elif I[int(dims[0]/2)-1,j]>-0.5:
            yL+=1   
    for i in range(x0,x0+xL):
        for j in range(y0,y0+yL):
            P=np.random.poisson(lam=255*I[i,j])
            G=np.random.normal(loc=0.0,scale=gauss)
            I[i,j]=G+poi*P/255.0+I[i,j]*(1-poi)
            if I[i,j]>1:
                I[i,j]=1.0
            if I[i,j]<0: #Note that the space of i,j here is not the backgroumd
                I[i,j]=0.0 
    # frame color will be taken care by add_color or separately for 
    # monochrome images

    return I

def intensity2image(I,dtype,axes='YX'):
    """ Converts float intensities to a different data type. Maximum intensity 
        is set to maxI.

    Parameters
    ----------
    I:
        see ''add_noise''
    dtype:
        Output image datatype 
    axes:
        Axes of I

    Returns
    -------
    I: Converted monochrome image with dtype
       XY axes images are changed to YX.
    bounds: bounds of the image returned in ZYX or YX format. 
    """
    maxI=np.iinfo(dtype).max
    consts=I.shape
    x0,xL,y0,yL=0,0,0,0
    bounds=[]
    if 'T' in axes:
        for i in range(consts[0]):
            bounds.append(get_bounds(I[i,:],axes[1:]))
    else:
        bounds.append(get_bounds(I,axes))

    I=I*maxI
    I[I>maxI]=maxI
    I[I<0]=0
   # if axes=='XY':
   #     I=np.transpose(I,(1,0))
   # if axes=='CXY':
   #     I=np.transpose(I,(0,2,1))

    return I.astype(dtype),bounds

def get_bounds(IMG,axes):
    I=copy.deepcopy(IMG) 
    # Axes of I can be YX, CYX, ZYX, ZCYX
    if axes=='CYX' or axes=='CXY':
        I=I[0,:,:]
    if axes=='ZCYX' or axes=='ZCXY':
        I=I[:,0,:,:]


    sha=I.shape
    if 'Z' in axes: #ZYX or ZCYX is equal to ZYX
                    #ZXY or ZCXY is equal to ZXY
        if axes=='ZXY' or axes=='ZCXY': 
            a=[0,sha[0],0,sha[2],0,sha[1]] #bounds are ZYX
        elif axes=='ZYX' or axes=='ZCYX':
            a=[0,sha[0],0,sha[1],0,sha[2]] #bounds are ZYX

        sha_mid=[int(x/2+0.5) for x in sha] 
        #0: mid of z, 1: mid of y, 2: mid of x
        for i in range(sha[2]):
            if I[0,sha_mid[1],i]==-1:
                a[0]+=1
            else: break
        for i in range(sha[2]):
            if I[0,sha_mid[1],sha[1]-1-i]==-1:
                a[1]-=1 
            else: break
        for j in range(sha[1]):
            if I[0,j,sha_mid[2]]==-1:
                a[2]+=1
            else: break
        for j in range(sha[1]):
            if I[0,sha[1]-1-j,sha_mid[2]]==-1:
                a[3]-=1 
            else: break
        for k in range(sha[0]):
            if I[k,sha_mid[1],sha_mid[2]]==-1:
                a[4]+=1
            else: break
        for k in range(sha[0]):
            if I[sha[0]-1-k,sha_mid[1],sha_mid[2]]==-1:
                a[5]-=1 
            else: break

    else: #YX or CYX is equal to YX
          #XY or CXY is equal to XY
        if axes=='CYX' or axes=='YX':
            a=[0,sha[0],0,sha[1]] #bounds are YX
        if axes=='CXY' or axes=='XY':
            a=[0,sha[1],0,sha[0]] #bounds are YX

        sha_mid=[int(x/2+0.5) for x in sha] 
        for i in range(sha[1]):
            if I[sha_mid[0],i]==-1:
                a[0]+=1
            else: break
        for i in range(sha[1]):
            if I[sha_mid[0],sha[1]-1-i]==-1:
                a[1]-=1 
            else: break
        for i in range(sha[0]):
            if I[i,sha_mid[1]]==-1:
                a[2]+=1
            else: break
        for i in range(sha[0]):
            if I[sha[0]-1-i,sha_mid[1]]==-1:
                a[3]-=1 
            else: break

    return a

def plot_lumin(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox):
    """ Interactively plot small portions of colored the in-silico microscopy
        image, the relative luminescence, and hue as a funciton in pixel 
        distance from the central pixel.

    Parameters
    ----------
    filename: str
        Filename header for image data file
    lam_I0s: 
        see ''get_col_img''
    lams:
        see ''get_col_img''
    lam_hues: 
        see ''get_col_img''
    T: 
        see ''get_grey_img''
    ti: 
        see ''get_grey_img''
    fs: 
        see ''get_grey_img''
    MaxBox: 
        see ''get_grey_img''
   
    Writes
    ------
        Ineteractively write the image generated in a custom filename.
    """
    col_IMGs=get_col_img(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox)
    consts=col_IMGs.shape
    img_hei=3.0
    img_width=consts[1]*img_hei/consts[0]
    fig,ax=plt.subplots(1, 1, figsize=(img_width, img_hei))
    ax.set_xticks([])
    ax.set_yticks([])
    plt.axis('off')
    plt.tight_layout(pad=0)
    ax.imshow(col_IMGs)
    plt.show(block=False)

    while True:
        print("Image dimensions are "+str(consts[0])+','+str(consts[1]))
        foo = input("Enter the pixel of interest (x,y): ")
        x,y=[int(x) for x in foo.split()]  
        width= int(input("Enter width in pixels: "))
        vals=[x,consts[0]-x,y,consts[1]-y]
        if min(vals)<width:
            width=min(vals)
        d=[]
        Lumin=[]
        Hue=[]
        for i in range(-width,width+1):
            for j in range(-width,width+1):
                d.append(np.sqrt(i**2+j**2)) 
                rgb=copy.deepcopy(col_IMGs[i+x,j+y,:])
                for k in range(3):
                   if rgb[k]<=0.03928:
                       rgb[k]=rgb[k]/12.92
                   else:
                       rgb[k]=((rgb[k]+0.055)/1.055)**2.4
                #Reference: https://www.w3.org/Graphics/Color/sRGB.html 
                #Check the published work for the accurate reference.
                hsv=rgb2hsv(rgb[0],rgb[1],rgb[2])
                Hue.append(hsv[0]*360)
                Lumin.append(0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2])
        fig,ax=plt.subplots(1, 3, figsize=(img_width*3, img_hei))
        ax[0].set_xticks([])
        ax[0].set_yticks([])
        ax[0].axis('off')
        ax[0].imshow(col_IMGs[x-width:x+width+1,y-width:y+width+1])
        ax[1].scatter(d,Lumin,c='k')
        ax[1].set_ylabel('Relative Luminance')
        ax[1].set_xlabel('Pixel distance')
        ax[2].scatter(d,Hue,c='k')
        ax[2].set_ylabel('Hue (deg)')
        ax[2].set_xlabel('Pixel distance')
        plt.tight_layout()
        plt.show(block=False)
        save=input("Save figure, contiune or quit (s/c/q)?")
        if save=='s':
            outname=input("Save as: ")
            foo=input("ylim for Lumin: ")
            ylim1,ylim2 = [float(x) for x in foo.split()]  
            foo=input("ylim for Hue: ")
            ylim3,ylim4 = [float(x) for x in foo.split()]  
            ax[0].set_xticks([])
            ax[0].set_yticks([])
            ax[0].axis('off')
            ax[0].imshow(col_IMGs[x-width:x+width+1,y-width:y+width+1])
            ax[1].scatter(d,Lumin,c='k')
            ax[1].set_ylabel('Relative Luminance')
            ax[1].set_xlabel('Pixel distance')
            ax[1].set_ylim(ylim1,ylim2)
            ax[2].scatter(d,Hue,c='k')
            ax[2].set_ylabel('Hue (deg)')
            ax[2].set_xlabel('Pixel distance')
            ax[2].set_ylim(ylim3,ylim4)
            plt.tight_layout()
            plt.savefig(outname,dpi=600)
            return
        elif save=='q':
            return


def get_region(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, \
    frame_col=1.0, mix_type='mt'):
    """ Calculates the image intensity for a region image,

    RGB color image is read. Colors are converted to HSV. Hues are changed to be 
    multiples of 10. Values are increased to 1, and the color is converted to 
    RGB.
     
    Parameters
    ----------
    filename: str
        Filename header for image data file
    lam_I0s: 
        see ''get_col_img''
    lams:
        see ''get_col_img''
    lam_hues: 
        see ''get_col_img''
    T: 
        see ''get_grey_img''
    ti: 
        see ''get_grey_img''
    fs: 
        see ''get_grey_img''
    MaxBox: 
        see ''get_grey_img''
    frame_col: 
        see ''get_grey_img''
    mix_type: 
        see ''get_col_img''
   
    Returns
    ------- 
    IMG: 3D ndarray
        Axis 2 corresponds to red, green and blue channels. Image intensities 
        between 0 and 1.
    """
    col_IMGs=get_col_img(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, 
        mix_type=mix_type)
    consts=col_IMGs.shape
    for i in range(consts[0]):
        for j in range(consts[1]):
            hsv=rgb2hsv(col_IMGs[i,j,0],col_IMGs[i,j,1],col_IMGs[i,j,2])
            hsv[0]=int(hsv[0]*36)/36
            rgb=hsv2rgb(hsv[0],hsv[1],1)
            col_IMGs[i,j,:]=rgb[:]
    return col_IMGs   

def plot_region(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, Bm,
    scale, dpi=600, outfile=None, frame_col=1.0):
    """ Plots color image by assigning a specific color for a region.
   
    Parameters
    ----------
    filename: str
        Filename header for image data file
    lam_I0s: 
        see ''get_col_img''
    lams:
        see ''get_col_img''
    lam_hues: 
        see ''get_col_img''
    T: 
        see ''get_grey_img''
    ti: 
        see ''get_grey_img''
    fs: 
        see ''get_grey_img''
    MaxBox: 
        see ''get_grey_img''
    Bm: 
        see ''add_scale''
    scale: 
        see ''add_scale''
    dpi:
        see ''plot_ism''
    outfile: str
        Output filename string
    frame_col: 
        see ''get_grey_img''
  
    Writes
    ------
    Writes a "region" image of in-silico microscopy image.
    """
    IMG=get_region(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox)
    IMG=add_scale(IMG, scale, Bm)
    if outfile!=None:
        plot_ism(IMG, lam_I0s, lams, T, ti, fs, filename='Reg_'+outfile, 
                 dpi=dpi, frame_col=frame_col)
    else:
        plot_ism(IMG, lam_I0s, lams, T, ti, fs, filename=None, dpi=dpi, 
                 frame_col=frame_col)


def plot_grey_img(filename, lam_I0s, lams, T, ti, fs, MaxBox, Bm, scale, 
    dpi=600, outfile=None, frame_col=1.0, noise=False, poi=None, gauss=None,
    otype='jpeg', psf_type=0, tsO=None, dlmn=None, pbc=None):
    """ Plots monochrome image with a scale.
    
    See functions get_grey_img, add_scale and plot_ism for more details.
    """
    for i in range(len(lams)):
        IMG=get_grey_img(filename, lam_I0s[i], lams[i], T, ti, fs, MaxBox, 
            frame=True, noise=noise, poi=poi, gauss=gauss, 
            psf_type=psf_type, tsO=tsO) #XY
        if otype in ['jpeg', 'png']:
            IMG=add_scale(IMG, scale, Bm)
        if outfile==None:
            outfile=filename
        plot_ism(IMG, [lam_I0s[i]], [lams[i]], T, ti, fs, filename=outfile,
                 dpi=dpi, otype=otype, psf_type=psf_type, tsO=tsO,
                 frame_col=frame_col, dlmn=dlmn, pbc=pbc)

def plot_col_img(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, dlmn, Bm, 
    scale, dpi=600, outfile=None, frame_col=1.0, mix_type='mt', noise=False,
    poi=None, gauss=None, otype='jpeg',psf_type=0, tsO=None, pbc=[1,1,1]):
    """ Plots coloured image with a scale.
    
    See functions get_col_img, add_scale and plot_ism for more details.
    """
    if outfile==None:
        outfile=filename
    IMG=get_col_img(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, 
        mix_type, noise=noise, poi=poi, gauss=gauss, psf_type=psf_type, 
        tsO=tsO) #IMG is XYC
    if otype in ['jpeg', 'png']:
        IMG=add_scale(IMG, scale, Bm)
    if mix_type=='none' or mix_type=='nomix': #will only plot tiff.
        IMG=np.transpose(IMG,(2,0,1)) #CXY
        IMG,bounds=intensity2image(IMG,'uint'+otype.split('f')[-1],axes='CXY')
        Istring=''
        for i in range(len(lam_I0s)):
            Istring+='_'+str(round(lam_I0s[i],4))
        tstr=''
        if psf_type==1:
            tstr='_tsO'+"%g"%tsO
        if ti>=0:#dynamic gro structure 
            fname=outfile + str(ti) + tstr + '_fs' + str(fs) + '_T' + str(T) + \
                  '_I' + Istring +'.tiff'
        else:# static gro structure
            fname=outfile + tstr + '_fs' + str(fs) + '_T' + str(T) + '_I' + \
                  Istring + '.tiff'
        print('Writing: '+fname)
        tif.imwrite(fname,IMG,photometric='minisblack',imagej=True, 
            resolution=(1./dlmn[0],1./dlmn[1]), metadata={'unit': 'nm', 
            'pbc': pbc, 'bounds': bounds, 'axes':'CYX'})

    else:
        plot_ism(IMG, lam_I0s, lams, T, ti, fs, filename=outfile, dpi=dpi, 
            otype=otype, psf_type=psf_type, tsO=tsO, frame_col=frame_col, 
            dlmn=dlmn, pbc=pbc)

def get_grey_3dimg(filename, lam_I0, lam, T, ti, fs, MaxBox, dlmn, nmax,
    opt_axis, add_n=1, outfile=None, otype='tiff8', mprocess=True, noise=False,
    poi=None, gauss=None, psf_type=0, tsO=None):
    """ Creates 3D monochrome images.

    See ''get_grey_img'' for details, lam_I0 is I0 in ''get_grey_img''
    Parameters
    ----------
    dlmn: array of floats
        Voxel dimensions in l,m,n direction. 
    nmax: int
    add_n: int
        Maximum coodinate in n direction is nmax*dlmn[2]. 3D images contains
        2D images from n=range(0,nmax,add_n)*dlmn[2].

    Returns
    -------
    img3d: 3D monochrome image. Axes ZXY.
    """

    nN=int(nmax/add_n)
    xyz='xyz'
    img3d=np.zeros((nN,MaxBox[0],MaxBox[1]),dtype='uint'+otype.split('f')[-1])
    #ZXY

    if mprocess==True: #Multiprocess
        Arguments=[]
        for n in range(nN):
            Arguments.append((filename, lam_I0, lam, T, ti, fs, MaxBox, True, \
                opt_axis, n*add_n, -1, noise, poi, gauss, psf_type, tsO))
        pool=mp.Pool(mp.cpu_count())
        results=pool.starmap(get_grey_img,Arguments)
    else: #Serial
        results=[]
        for n in range(nN):
            results.append(get_grey_img(filename, lam_I0, lam, T, ti, fs,
                MaxBox, True, opt_axis, n*add_n, -1, noise, poi, gauss,
                psf_type, tsO))
    cnt,z0,zL=0,0,nN
    for n in range(nN):
        foo,bounds_i=intensity2image(results[n],img3d.dtype,axes='XY')
        if bounds_i[0][0]>bounds_i[0][1] and bounds_i[0][2]>bounds_i[0][3] \
            and cnt==1:
            zL=n
            cnt=2
        if bounds_i[0][0]<bounds_i[0][1] and bounds_i[0][2]<bounds_i[0][3] \
            and cnt==0:
            bounds=copy.deepcopy(bounds_i)
            z0=n
            cnt=1
        img3d[nN-n-1,:,:]=foo[:,:]
    bounds[0]=[z0,zL]+bounds[0]
    return img3d, bounds

def plot_grey_3dimg(filename, lam_I0s, lams, T, ti, fs, MaxBox, dlmn, nmax,
    opt_axis, add_n=1, outfile=None, otype='tiff8', mprocess=True, noise=False,
    poi=None, gauss=None, psf_type=0, tsO=None, pbc=[1,1,1]):
    """ Plots monochrome 3D image. See ''get_grey_3dimg'' for details.

    Parameters
    ----------
    lam_I0s: see ''get_col_img''
    lams:    see ''get_col_img''
    """
    if outfile==None:
        outfile=filename
    tstr=''
    xyz='xyz'
    if psf_type==1:
        tstr='_tsO'+"%g"%tsO
    for l in range(len(lams)):
        img3d,bounds=get_grey_3dimg(filename, lam_I0s[l], lams[l], T, ti, fs, 
            MaxBox, dlmn, nmax, opt_axis, add_n=add_n, outfile=outfile, 
            otype=otype, mprocess=mprocess, noise=noise, poi=poi, gauss=gauss, 
            psf_type=psf_type, tsO=tsO)
        oname=outfile +str(ti) +'_'+xyz[opt_axis] +tstr +'_lam'+str(lams[l]) +\
            '_fs'+str(fs) +'_T'+str(T) +'_I'+str(lam_I0s[l]) +'.tiff'
        print('Writing: '+oname)
        tif.imwrite(oname, img3d, imagej=True, resolution=(1./dlmn[0], 
             1./dlmn[1]), metadata={'spacing': dlmn[2], 'unit': 'nm', 
             'axes': 'ZYX', 'bounds': bounds, 'pbc':pbc})
    
def plot_grey_3dtimg(filename, lam_I0s, lams, T, tbegin, tmax, tdiff, fs, 
    MaxBox, dlmn, nmax, opt_axis, fpns, add_n=1, outfile=None, otype='tiff8', 
    mprocess=True, noise=False, poi=None, gauss=None, psf_type=0, tsO=None, 
    pbc=[1,1,1]):
    """ Plots 3DT monochrome image. See ''plot_grey_3dimg'' for details.

    Parameters
    ----------
    tbegin: int
        index of first timestep, which is included.
    tmax: int
        index of maximum timestep, tmax is not included.
    tdiff: int 
        difference between timesteps to generate the 3DT image.
    fpns: int
        Frames per nano-second for the output tiff file.
  
    Returns
    -------
    img3dt: 3DT monochrome image. Axes TZXY.
    """
    if outfile==None:
        outfile=filename

    nN=int(nmax/add_n)
    tN=int((tmax-1-tbegin)/tdiff)+1
    xyz='xyz'
    img3dt=np.zeros((tN,nN,MaxBox[0],MaxBox[1]),dtype='uint'+ \
        otype.split('f')[-1]) #TZXY
    tstr=''
    if psf_type==1:
        tstr='_tsO'+"%g"%tsO
    #Check if all tiff exists
    nname=''
    if noise:
        nname='noise_'
    for l in range(len(lams)):
        bounds=[]
        for i in range(tN):
            ti=tbegin+tdiff*i
            img3d, bound=get_grey_3dimg(filename, lam_I0s[l], lams[l], T, ti, 
                fs, MaxBox, dlmn, nmax, opt_axis, add_n=add_n, outfile=outfile, 
                otype=otype, mprocess=mprocess, noise=noise, poi=poi, 
                gauss=gauss, psf_type=psf_type, tsO=tsO) #ZXY
            bounds+=bound
            img3dt[i,:,:,:]=img3d[:,:,:]
        oname=outfile +str(tbegin)+'-'+str(tmax) + '_'+xyz[opt_axis] +tstr + \
            '_lam'+str(lams[l]) +'_fs'+str(fs) +'_T'+str(T) +'_I'+ \
            str(lam_I0s[l]) +'.tiff'
        print('Writing: '+oname)
        tif.imwrite(oname, img3dt, imagej=True, resolution=(1./dlmn[0], 
            1./dlmn[1]), metadata={'spacing': dlmn[2], 'unit': 'nm', 
            'finterval': fpns, 'funit': 'ns', 'axes': 'TZYX', 
            'bounds': bounds, 'pbc':pbc})

def plot_grey_2dtimg(filename, lam_I0s, lams, T, tbegin, tmax, tdiff, fs, 
    MaxBox, dlmn, fpns, outfile=None, otype='tiff8', mprocess=True, noise=False,
    poi=None, gauss=None, psf_type=0, tsO=None, pbc=[1,1,1]):
    """ Plots 2DT monochrome image. See ''get_grey_3dtimg'' for more details.

    """
    if outfile==None:
        outfile=filename 
    tN=int((tmax-1-tbegin)/tdiff)+1
    img2dt=np.zeros((tN,MaxBox[0],MaxBox[1]),dtype='uint'+ \
        otype.split('f')[-1]) #TXY
    tstr=''
    if psf_type==1:
        tstr='_tsO'+"%g"%tsO
    #Check if all tiff exists
    for l in range(len(lams)):
        if mprocess==True: #Multiprocess
            Arguments=[]
            for i in range(tN):
                ti=tbegin+tdiff*i
                Arguments.append((filename, lam_I0s[l], lams[l], T, ti, fs, 
                    MaxBox, True, None, None, 0, noise, poi, gauss, 
                    psf_type, tsO))
            pool=mp.Pool(mp.cpu_count())
            results=pool.starmap(get_grey_img,Arguments) #Images are in XY
        else: #Serial
            results=[]
            for i in range(tN):
                ti=tbegin+tdiff*i
                results.append(get_grey_img(filename, lam_I0s[l], lams[l], T, 
                    ti, fs, MaxBox, True, None, None, 0, noise, poi, gauss,
                    psf_type, tsO)) #Images are in XY
        bounds=[]
        for i in range(tN):
            foo,bound=intensity2image(results[i],img2dt.dtype,axes='XY') 
            bounds+=bound
            img2dt[i,:,:]=foo[:,:]
        oname=outfile +str(tbegin)+'-'+str(tmax) +tstr +'_lam'+str(lams[l]) + \
            '_fs'+str(fs) +'_T'+str(T) +'_I'+str(lam_I0s[l]) +'.tiff'
        print('Writing: '+oname)
        tif.imwrite(oname, img2dt, imagej=True, resolution=(1./dlmn[0], 
            1./dlmn[1]), metadata={'unit': 'nm', 'finterval': fpns, 
            'funit': 'ns', 'axes': 'TYX', 'bounds':bounds, 'pbc':pbc})

def get_col_3dimg(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, dlmn, 
    nmax, opt_axis, add_n=1, outfile=None, otype='tiff8', mprocess=True, 
    noise=False, poi=None, gauss=None, mix_type='mt', psf_type=0, tsO=None):
    """ Creates 3D color images. See ''get_col_img'' for details. For dlmn,
        nmax, add_n see ''get_grey_3dimg''.

    Returns
    -------
    img3d: 3D monochrome image. Axes ZCXY.
    """
    nN=int(nmax/add_n)
    xyz='xyz'
    C=3 #3 color channels for 'mt' image
    if mix_type=='none' or mix_type=='nomix': #Colors are not mixed.
        C=len(lams)
    img3d=np.zeros((nN,C,MaxBox[0],MaxBox[1]),dtype='uint'+ \
        otype.split('f')[-1]) #ZCXY
    if mprocess==True: #Multiprocess
        Arguments=[]
        for n in range(nN):
            Arguments.append((filename, lam_I0s, lams, lam_hues, T, ti, fs, 
                MaxBox, mix_type, opt_axis, n*add_n, noise, poi, gauss,
                psf_type, tsO)) #XYC
        pool=mp.Pool(mp.cpu_count())
        results=pool.starmap(get_col_img,Arguments)
        pool.close()
    else: #Serial
        results=[]
        for n in range(nN):
            results.append(get_col_img(filename, lam_I0s, lams, lam_hues, 
                T, ti, fs, MaxBox, mix_type, opt_axis, n*add_n, 
                noise, poi, gauss, psf_type, tsO))#XYC
    cnt=0 
    for n in range(nN):
        foo=np.transpose(results[n],(2,0,1)) # Change foo from XYC to CXY
        foo,bounds_i=intensity2image(foo,img3d.dtype,axes='CXY') 
        if bounds_i[0][0]>bounds_i[0][1] and bounds_i[0][2]>bounds_i[0][3] \
            and cnt==1:
            zL=n
            cnt=2
        if bounds_i[0][0]<bounds_i[0][1] and bounds_i[0][2]<bounds_i[0][3] \
            and cnt==0:
            bounds=copy.deepcopy(bounds_i)
            z0=n
            cnt=1
        img3d[nN-n-1,:,:,:]=foo[:,:,:] 
    bounds[0]=[z0,zL]+bounds[0]
    return img3d,bounds

def plot_col_3dimg(filename, lam_I0s, lams, lam_hues, T, ti, fs, MaxBox, dlmn, 
    nmax, opt_axis, add_n=1, outfile=None, otype='tiff8', mprocess=True, 
    noise=False, poi=None, gauss=None, mix_type='mt', psf_type=0, tsO=None, 
    pbc=[1,1,1]):
    """ Plots 3D color images. See ''get_col_3dimg'' for details.

    """
    if outfile==None:
        outfile=filename
    Istring=''
    xyz='xyz'
    for i in range(len(lams)):
        Istring+='_'+str(lam_I0s[i])
    tstr=''
    if psf_type==1:
        tstr='_tsO'+"%g"%tsO
    img3d, bounds=get_col_3dimg(filename, lam_I0s, lams, lam_hues, T, ti, fs, 
        MaxBox, dlmn, nmax, opt_axis, add_n=add_n, outfile=outfile, otype=otype, 
        mprocess=mprocess, noise=noise, poi=poi, gauss=gauss, mix_type=mix_type,
        psf_type=psf_type, tsO=tsO)

    oname=outfile+str(ti) + '_'+xyz[opt_axis] +tstr +'_fs'+str(fs) +'_T' + \
        str(T) +'_I'+Istring+'.tiff'
    print('Writing: '+oname)
    tif.imwrite(oname, img3d, imagej=True, resolution=(1./dlmn[0],1./dlmn[1]),
        metadata={'spacing': dlmn[2], 'unit': 'nm', 'axes': 'ZCYX', 
            'bounds': bounds, 'pbc':pbc})

def plot_col_3dtimg(filename, lam_I0s, lams, lam_hues, T, tbegin, tmax, tdiff, 
    fs, MaxBox, dlmn, nmax, opt_axis, fpns, add_n=1, outfile=None, 
    otype='tiff8', mprocess=True, noise=False, poi=None, gauss=None, 
    mix_type='mt', psf_type=0, tsO=None, pbc=[1,1,1]):
    """ Plots 3DT color image. See ''get_col_3dimg'' for details. For tbegin, 
        tmax, tdiff, and fpns see ''plot_grey_3dtimg''.

    """
    if outfile==None:
        outfile=filename
    nN=int(nmax/add_n)
    tN=int((tmax-1-tbegin)/tdiff)+1
    C=3 #3 color channels for 'mt' image
    if mix_type=='none' or mix_type=='nomix': #Colors are not mixed.
        C=len(lams)
    
    xyz='xyz'
    img3dt=np.zeros((tN,nN,C,MaxBox[0],MaxBox[1]),dtype='uint'+ \
        otype.split('f')[-1]) #TZCXY
    Istring=''
    for i in range(len(lams)):
        Istring+='_'+str(lam_I0s[i])
    tstr=''
    if psf_type==1:  
        tstr='_tsO'+"%g"%tsO
    bounds=[]
    #Check if all tiff exists
    for i in range(tN):
        ti=tbegin+tdiff*i
        img3d,bound=get_col_3dimg(filename, lam_I0s, lams, lam_hues, T, ti, fs,
            MaxBox, dlmn, nmax, opt_axis, add_n=add_n, outfile=outfile, 
            otype=otype, mprocess=mprocess, noise=noise, poi=poi,
            gauss=gauss, mix_type=mix_type, psf_type=psf_type, tsO=tsO) # ZCXY
        bounds+=bound
        img3dt[i,:,:,:,:]=img3d[:,:,:,:]
    oname=outfile +str(tbegin)+'-'+str(tmax) +'_' +xyz[opt_axis] +tstr + \
        '_fs'+str(fs) +'_T'+str(T)+ '_I'+Istring +'.tiff'
    print('Writing: '+oname)
    tif.imwrite(oname, img3dt, resolution=(1./dlmn[0],1./dlmn[1]), imagej=True,
        metadata={'spacing': dlmn[2], 'unit': 'nm', 'finterval': fpns, 
            'funit': 'ns', 'axes': 'TZCYX', 'bounds': bounds, 'pbc':pbc})

def plot_col_2dtimg(filename, lam_I0s, lams, lam_hues, T, tbegin, tmax, tdiff, 
    fs, MaxBox, fpns, dlmn, outfile=None, otype='tiff8', mprocess=True, 
    noise=False, poi=None, gauss=None, mix_type='mt', psf_type=0, tsO=None, 
    pbc=[1,1,1]):
    """ Plots 2DT color image. see ''plot_col_3dtimg'' for details.

    """ 
    if outfile==None:
        outfile=filename
    tN=int((tmax-1-tbegin)/tdiff)+1
    C=3 #3 color channels for 'mt' image
    if mix_type=='none' or mix_type=='nomix': #Colors are not mixed.
        C=len(lams)
    
    img2dt=np.zeros((tN,C,MaxBox[0],MaxBox[1]),dtype='uint'+ \
        otype.split('f')[-1]) #TCXY
    Istring=''
    for i in range(len(lams)):
        Istring+='_'+str(lam_I0s[i])
    tstr=''
    if psf_type==1:
        tstr='_tsO'+"%g"%tsO
    #Check if all tiff exists
    if mprocess==True: #Multiprocess
        Arguments=[]
        for i in range(tN):
            ti=tbegin+tdiff*i
            Arguments.append((filename, lam_I0s, lams, lam_hues, T, ti, fs, 
                MaxBox, mix_type, None, None, noise, poi, gauss, psf_type,
                tsO)) #XYC
        pool=mp.Pool(mp.cpu_count())
        results=pool.starmap(get_col_img,Arguments)
        pool.close()
    else: #Serial
        results=[]
        for i in range(tN):
            ti=tbegin+tdiff*i
            results.append(get_col_img(filename, lam_I0s, lams, lam_hues, T, ti, 
                fs, MaxBox, mix_type, None, None, noise, poi, gauss,
                psf_type, tsO)) #XYC
    bounds=[]
    for i in range(tN):
        foo=np.transpose(results[i],(2,0,1)) #Change foo from XYC to CXY
        foo,bound=intensity2image(foo,img2dt.dtype,axes='CXY')
        bounds+=bound
        img2dt[i,:,:,:]=foo[:,:,:]
    oname=outfile +str(tbegin)+'-'+str(tmax) +tstr +'_fs'+str(fs) +'_T' + \
          str(T) +'_I'+Istring +'.tiff'
    print('Writing: '+oname)
    #fpns is frames per nano-second.
    tif.imwrite(oname, img2dt, resolution=(1./dlmn[0],1./dlmn[1]), imagej=True, 
        metadata={ 'unit': 'nm', 'finterval': fpns, 'funit': 'ns', 
            'bounds': bounds, 'pbc':pbc, 'axes': 'TCYX'})

def plot_grey_serial(filename, lam_I0s, lams, T, tbegin, tmax, tdiff, fs, 
    MaxBox, Bm, scale, dpi, outname, frame_col, noise, poi, gauss, otype, 
    psf_type, tsO, dlmn, pbc):
    """ Plots several monochrome images serially.

    See plot_grey_img for more details.
    """
    for i in range(tbegin,tmax,tdiff):
        plot_grey_img(filename, lam_I0s, lams, T, i, fs, MaxBox, Bm, scale, dpi, 
                      outname, frame_col, noise, poi, gauss, otype, psf_type,
                      tsO, dlmn, pbc)

    
def plot_col_serial(filename, lam_I0s, lams, lam_hues, T, tbegin, tmax, tdiff, 
    fs, MaxBox, Bm, scale, dpi, outname, frame_col, mix_type, noise, poi, gauss, 
    otype, psf_type, tsO, dlmn, pbc):
    """ Plots several coloured images serially.

    See plot_col_img for more details.
    """
    for i in range(tbegin,tmax,tdiff):
        plot_col_img(filename, lam_I0s, lams, lam_hues, T, i, fs, MaxBox, dlmn, 
            Bm, scale, dpi, outname, frame_col, mix_type, noise, poi, gauss, 
            otype, psf_type, tsO, pbc)

def plot_grey_mp(filename, lam_I0s, lams, T, tbegin, tmax, tdiff, fs, MaxBox, 
    Bm, scale, dpi, output, frame_col, noise, poi, gauss, otype, psf_type, tsO,
    dlmn, pbc):
    """ Plots several monochrome images parallelly.

    See plot_grey_img for more details.
    """

    Arguments=[]
    for i in range(tbegin,tmax,tdiff): 
        Arguments.append([filename, lam_I0s, lams, T, i, fs, MaxBox, Bm, scale, 
                          dpi, output, frame_col, noise, poi, gauss, otype,
                          psf_type, tsO, dlmn, pbc])
    cpus=mp.cpu_count()
    if len(Arguments)<cpus:
        cpus=len(Arguments)
    pool=mp.Pool(cpus)
    results=pool.starmap(plot_grey_img,Arguments)
    pool.close()

def plot_col_mp(filename, lam_I0s, lams, lam_hues, T, tbegin, tmax, tdiff, fs, 
    MaxBox, Bm, scale, dpi, output, frame_col, mix_type, noise, poi, gauss,
    otype, psf_type, tsO, dlmn, pbc):
    """ Plots several coloured images parallely.

    See plot_col_img for more details.
    """
    Arguments=[]
    for i in range(tbegin,tmax,tdiff):
        Arguments.append([filename, lam_I0s, lams, lam_hues, T, i, fs, MaxBox, 
            dlmn, Bm, scale, dpi, output,frame_col, mix_type, noise, poi, gauss, 
            otype,psf_type,tsO, pbc])
    cpus=mp.cpu_count()
    if len(Arguments)<cpus:
        cpus=len(Arguments)
    pool=mp.Pool(cpus)
    results=pool.starmap(plot_col_img,Arguments)
    pool.close()
