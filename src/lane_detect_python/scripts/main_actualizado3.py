#!/usr/bin/python
# -*- coding: latin-1 -*-
from __future__ import print_function
import roslib
roslib.load_manifest('lane_detect_python')
import sys
import rospy
import cv2
import numpy as np
from std_msgs.msg import String
from std_msgs.msg import Float32
from std_msgs.msg import Int16
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import numpy.polynomial as P
import math

ransac_iterations = 17  # number of iterations
ransac_threshold = 2# threshold
ransac_ratio = 0.97 # ratio of inliers required to assert
                        # that a model fits well to data
n_inputs = 1
n_outputs = 1
obstaculo=True
conta=0
ang=0
contador=0

def find_line_model(points):
 
    # [WARNING] vertical and horizontal lines should be treated differently
    #           here we just add some noise to avoid division by zero
 
    # find a line model for these points
    m = (points[1,1] - points[0,1]) / (points[1,0] - points[0,0]+ sys.float_info.epsilon)  # slope (gradient) of the line
    c = points[1,1] - m * points[1,0]    
           # y-intercept of the line
    return m, c, points
    
def find_intercept_point(m, c, x0, y0):
    # intersection point with the model
    x = (x0 + m*y0 - m*c)/(1 + m**2)
    y = (m*x0 + (m**2)*y0 - (m**2)*c)/(1 + m**2) + c
 
    return x, y      
    
    
class image_converter:

  def __init__(self):
    self.image_pub = rospy.Publisher("image_topic_2",Image,queue_size=1)

    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber("/app/camera/rgb/image_raw",Image,self.callback)
    self.osbt_sub = rospy.Subscriber("obstacle_front", String, self.callback_obst)
    self.park_sub = rospy.Subscriber("parking_speed_cmd", Int16, self.callback_park)
    self.pub_ang = rospy.Publisher("/angle_lane", Float32, queue_size=1)
    self.pub_cross = rospy.Publisher("/cross", Int16, queue_size=1)

    self.conta=0
    self.conta_obs=0
    self.contador=0
    self.ang=0
    self.park_flg=False
    self.lado_inicial=1
    self.conta_crucero=0
    self.conta_no_crucero=0
    

    
  def callback_park(self,data):
    self.park_flg=True

  def callback_obst(self,data):
    if (data.data=="obstaculo"):
        self.conta+=1
        if (self.conta%30):
            print('obstaculo_recibido')



  def callback(self,data):
    
    if (self.conta%4==0):
        try:
          #cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
          frame = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
          print(e)




            #_, frame = cap.read()    
        frame = cv2.resize(frame, (160,120))
    
        (rows,cols,channels) = frame.shape
        tam_crop_g=41#33
        tam_crop=tam_crop_g/2
        tam_crop2=0
        crop_img = frame[rows-tam_crop_g:rows, tam_crop2:cols-tam_crop2]
        
        
        #crop_img = cv2.resize(crop_img, (160,tam_crop_g/2)) 
        #(row,col,v) = crop_img.shape
        #print(row)
        #print(col)
        offsetx=45 +20 
        #gray2 = cv2.cvtColor(resized_image,cv2.COLOR_BGR2GRAY)  
            
        gray = cv2.cvtColor(crop_img,cv2.COLOR_BGR2GRAY)  
            
        (rows3,cols3) = gray.shape
        
        correct=39
        elong=100    
        way=np.array([[correct,0],[0,tam_crop],[cols3,tam_crop],[cols3-correct,0]],dtype="float32")#chidocam_coche_res
        nwy=np.array([[offsetx+0,0],[offsetx+0,tam_crop+elong],[offsetx+ cols3,tam_crop+elong],[offsetx+cols3,0]],dtype="float32")#chidocam_coche_res    
        M=cv2.getPerspectiveTransform(way,nwy)
       
        
        phi=.85#.62
        theta=1.4#1.98
        maxIntensity=255.0
        gray3=(maxIntensity/phi)*(gray/(maxIntensity/theta))**8
        gray3[np.where(gray3<00)]=0
        gray3[np.where(gray3>250)]=255
        gray3 =(np.uint8(gray3))
        gray4=cv2.warpPerspective(gray3,M,(cols3+(correct*2)+50,rows3+elong+10))
        #ret, thresh = cv2.threshold(gray3,20,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        ret, thresh = cv2.threshold(gray4,50,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        #sobelx = cv2.Sobel(thresh,cv2.CV_64F,1,0,ksize=3)#derivada para imágen
        sobelx=cv2.Canny(thresh,250,250,apertureSize = 3)
        #abs_sobel=np.absolute(sobelx)
        #sobelx=np.uint8(abs_sobel)
        gray = cv2.resize(sobelx, (200,105))

        cv2.line(sobelx,(0,14),(57,105),(0,0,0),5)    
        #cv2.line(sobelx,(0,77),(21,96),(255,255,255),2)    
        cv2.line(sobelx,(200,14),(143,105),(0,0,0),5)

        (rowss,colss) = sobelx.shape
        #sobelx = sobelx[30:rowss, 0:colss]
        (rows3,cols3) = sobelx.shape
        #print(rows3)
        #print(cols3)
        #print(rows3)
        #print(cols3)#tamaño 110 85

        #cv2.line(sobelx,(97,85),(121,0),(255,255,255),2)
        warped=sobelx    
        (rows2,cols2)=warped.shape
        num_lin=20

        #*******************************************
        #**************************************
        #********************************
        #*****************************************
        num_lin2=30
        rws=np.round(np.linspace(cols2-1,0,num_lin2))#dividimos en diferentes regiones        
        arreglo=np.where(warped[:,[rws]])#deteccion de puntos blanco en cada linea en que se dividió
        #rws=np.round(np.linspace(rows2-1,0,num_lin))#dividimos en diferentes regiones        
        #arreglo=np.where(warped[[rws],:])#deteccion de puntos blanco en cada linea en que se dividió
        
        #rws=np.round(np.linspace(rows2-1,0,num_lin))#dividimos en diferentes regiones        
        #arreglo=np.where(warped[[rws],:])#deteccion de puntos blanco en cada linea en que se dividió
        arreglo=np.asarray(sorted(zip(arreglo[0],arreglo[2]),key=lambda e:e[1]))
        pr=0
        valor=list()
        lista=list()
        aux=(0,0)
        suma=0
        #############################################
        #arreglo de puntos donde se descartan puntos cercanos se promedia para obtener un solo puntos
        init_flag=False 
        for idx in arreglo[:,1]:
            #new_p=(arreglo[2][pr],int(rws[idx]))    
           # new_p=(int(rws[idx]),arreglo[0][pr])    
            new_p=(arreglo[:,0][pr],int(rws[idx]))    
            pr=pr+1 
            if init_flag==False:
                valor.append(new_p[0])
                aux=new_p
                init_flag=True
            else: 
                if new_p[1]==aux[1] and (new_p[0]<aux[0]+22 and new_p[0]>aux[0]-22):
                    valor.append(new_p[0])
                else: #new_p[1]>aux[1]:
                    if len(valor)>0:## promedio para un solo punto
                        for i in range(0,len(valor)):
                            suma=suma+valor[i]
                        prom=suma/len(valor)
                        #nue=(prom,aux[1])
                        nue=(aux[1],prom)
                        cv2.circle(warped,nue, 2, (255,255,255),2)
                        lista.append(nue)
                    suma=0
                    valor=[]
                    valor.append(new_p[0])
                aux=new_p
        ls=np.asarray(lista)
        ordp=[]
        ordp.append([])
        ##################################################
        #y=ls[:,1]
        #x=ls[:,0] 
        y=ls[:,1]
        x=ls[:,0]
        centro=round(cols2/2)#centro de la imágen del cochesito
        
        #####################################################3
        ## SE GENERAN LISTAS DE CADA LINEA
        for val in ls:
            if len(ordp[0])==0:#lista nueva no inicializad
                ordp[0].append(val)
            else:
                len(ordp)
                flag=False
                for i in range(0,len(ordp)):
                    if np.abs(val[0]-ordp[i][len(ordp[i])-1][0])<5 and np.abs(val[1]-ordp[i][len(ordp[i])-1][1])<=(rws[0]-rws[2]):
                        ordp[i].append(val)
                        flag=True
                        break
                    elif i==len(ordp)-1 and flag==False:
                        ordp.append([])
                        ordp[i+1].append(val)
        ############################################################
        #################################################################3                    
        ######SE DESCARTAN LINEAS
        #tam_carril=55#Es el tamaño de carril a detectar y a dibujar si o existe otro
        #value=[]
        #holg=14
        #flg2=True
        #n=0                  
        for x in range(0,len(ordp)):
            if (ordp[x][0][1]>0) and (len(ordp[x])>10):##LIMITE Y y LIMITE DE TAMAÑO
                print("crucero!!!!!!!!!!")
                self.conta_crucero+=1
                if(self.conta_crucero>5):
                    self.conta_no_crucero=0
                    self.pub_cross.publish(1)
            elif (self.conta_crucero>5):
                self.conta_no_crucero+=1
                if (self.conta_no_crucero>25):
                    self.conta_crucero=0
                    self.pub_cross.publish(0)
                    self.pub_cross.publish(0)
                    self.pub_cross.publish(0)
                    self.conta_no_crucero=0


                        

                #value.append([x,(ordp[x][1][0]-centro),len(ordp[x]),ordp[x][1][0]])
       

    #******************************
    #**********************************
    #*******************************
    #***********************









        rws=np.round(np.linspace(rows2-1,0,num_lin))#dividimos en diferentes regiones        
        arreglo=np.where(warped[[rws],:])#deteccion de puntos blanco en cada linea en que se dividió

        pr=0
        valor=list()
        lista=list()
        aux=(0,0)
        suma=0
        #############################################
        #arreglo de puntos donde se descartan puntos cercanos se promedia para obtener un solo puntos
        init_flag=False 
        for idx in arreglo[1]:
            new_p=(arreglo[2][pr],int(rws[idx]))    
            pr=pr+1 
            if init_flag==False:
                valor.append(new_p[0])
                aux=new_p
                init_flag=True
            else: 
                if new_p[1]==aux[1] and (new_p[0]<aux[0]+15 and new_p[0]>aux[0]-15):
                    valor.append(new_p[0])
                else: #new_p[1]>aux[1]:
                    if len(valor)>0:## promedio para un solo punto
                        for i in range(0,len(valor)):
                            suma=suma+valor[i]
                        prom=suma/len(valor)
                        nue=(prom,aux[1])
                        cv2.circle(warped,nue, 2, (255,255,255),2)
                        lista.append(nue)
                    suma=0
                    valor=[]
                    valor.append(new_p[0])
                aux=new_p
        ls=np.asarray(lista)
        ordp=[]
        ordp.append([])
        ##################################################
        y=ls[:,1]
        x=ls[:,0] 
        centro=round(cols2/2)#centro de la imágen del cochesito
        
        #####################################################3
        ## SE GENERAN LISTAS DE CADA LINEA
        for val in ls:
            if len(ordp[0])==0:#lista nueva no inicializad
                ordp[0].append(val)
            else:
                len(ordp)
                flag=False
                for i in range(0,len(ordp)):
                    if np.abs(val[0]-ordp[i][len(ordp[i])-1][0])<20 and np.abs(val[1]-ordp[i][len(ordp[i])-1][1])<=(rws[0]-rws[7]):
                        ordp[i].append(val)
                        flag=True
                        break
                    elif i==len(ordp)-1 and flag==False:
                        ordp.append([])
                        ordp[i+1].append(val)
        ############################################################
        #################################################################3                    
        ######SE DESCARTAN LINEAS
        tam_carril=70#Es el tamaño de carril a detectar y a dibujar si o existe otro
        value=[]
        holg=24
        n=0                  
        for x in range(0,len(ordp)):
            if (ordp[x][0][1]>0) and (len(ordp[x])>6):##LIMITE Y y LIMITE DE TAMAÑO
                value.append([x,(ordp[x][1][0]-centro),len(ordp[x]),ordp[x][1][0]])
        value=np.asarray(sorted(value,key=lambda x:x[2]))
       # print(value)
        ind1=np.argmin(abs(value[:,1]))##lugar del minimo al centro  
        indice=int(value[ind1][0]) ##lugar en ordp del minimo al centro
        #print(indice) 
      #########################################################################
        ## Se detecta el carril     

       
        gen1=False
        gen2=False
        genextra=False
        rside=True
        
        
         
        if len(value)>2:##tres carriles
            #if np.sign(value[np.argmax(value[:,2]),1])==self.lado:##self.lado correcto
            lado=np.sign(value[np.argmax(value[:,2]),1])##izquierda -1 derecha 1
            if lado==self.lado_inicial:
                aseguir1=value[np.argmax(value[:,2])]
                sobrante=value[np.where(np.sign(value[:,1])!=lado)]##posible lineas a carril
                sobrante[:,1]=sobrante[:,1]-value[np.argmax(value[:,2]),1]##tamaños de carril en [1]
                aseguir2=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril-holg,abs(sobrante[:,1])<tam_carril+holg],0))]
                if len(aseguir2)==0:##carril fuera de rango 
                    gen2=True            
                else:
                    aseguir2=aseguir2[0]
            
                extra=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril*2-holg,abs(sobrante[:,1])<tam_carril*2+holg],0))]
                if len(extra)==0:##Extra fuera de rango 
                    genextra=True
                else:
                    extra=extra[0]
            elif len(np.delete(value,np.where(np.sign(value[:,1])==self.lado_inicial),0))==2:
                ##estamos en el carril correcto
                aseguir1=value[np.where(np.sign(value[:,1])==self.lado_inicial)]
                sobrante=value[np.where(np.sign(value[:,1])!=self.lado_inicial)]##posible lineas a carril
                sobrante[:,1]=sobrante[:,1]-aseguir1[1]##tamaños de carril en [1]
                aseguir2=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril-holg,abs(sobrante[:,1])<tam_carril+holg],0))]
                if len(aseguir2)==0:##carril fuera de rango 
                    gen2=True            
                else:
                    aseguir2=aseguir2[0]
            
                extra=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril*2-holg,abs(sobrante[:,1])<tam_carril*2+holg],0))]
                if len(extra)==0:##Extra fuera de rango 
                    genextra=True
            elif len(np.delete(value,np.where(np.sign(value[:,1])==self.lado_inicial),0))==1:
                ##otro carril
                aseguir1=value[np.argmax(abs(value[:,1]))]
                sobrante=np.delete(value,np.argmax(abs(value[:,1])),0)
                sobrante[:,1]=sobrante[:,1]-aseguir1[1]#tamaños de carril en [1]
                aseguir2=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril-holg,abs(sobrante[:,1])<tam_carril+holg],0))]
                if len(aseguir2)==0:##carril fuera de rango 
                    gen2=True            
                else:
                    aseguir2=aseguir2[0]
            
                extra=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril*2-holg,abs(sobrante[:,1])<tam_carril*2+holg],0))]
                if len(extra)==0:##Extra fuera de rango 
                    genextra=True       
                
        elif len(value)==2:
            
            if np.sign(value[np.argmax(value[:,2]),1])==self.lado_inicial:##lado correcto
                lado=np.sign(value[np.argmax(value[:,2]),1])##izquierda -1 derecha 1#Actualizar
                aseguir1=value[np.argmax(value[:,2])]
                sobrante=value[np.where(np.sign(value[:,1])!=self.lado_inicial)]##posible lineas a carril
                sobrante[:,1]=sobrante[:,1]-value[np.argmax(value[:,2]),1]##tamaños de carril en [1]
                aseguir2=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril-holg,abs(sobrante[:,1])<tam_carril+holg],0))]
                if len(aseguir2)==0:
                    gen2=True
                else:
                    aseguir2=aseguir2[0]
                genextra=True
                
            elif np.sign(value[np.argmax(value[:,2]),1])!=self.lado_inicial and np.sign(value[np.argmin(value[:,2]),1])==self.lado_inicial:
                ##Es el mismo carril pero se achico la orilla
                aseguir1=value[np.argmin(value[:,2])]
                rside=True#False#True
                sobrante=value[np.where(np.sign(value[:,1])!=self.lado_inicial)]##posible lineas a carril
                sobrante[:,1]=sobrante[:,1]-value[np.argmin(value[:,2]),1]##tamaños de carril en [1]
                aseguir2=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril-holg,abs(sobrante[:,1])<tam_carril+holg],0))]
                if len(aseguir2)==0:
                    gen2=True
                else:
                    aseguir2=aseguir2[0]
                genextra=True

            else: ##se alcanza a ver otro carril 
                gen1=True
                aseguir2=value[ind1]
                sobrante=np.delete(value,ind1,0)
                sobrante[:,1]=sobrante[:,1]-value[ind1,1]##tamaños de carril en [1]
                extra=sobrante[np.where(np.all([abs(sobrante[:,1])>tam_carril-holg,abs(sobrante[:,1])<tam_carril+holg],0))]
                
                if len(extra)==0:
                    genextra=True
                else:
                    extra=extra[0]
                
        elif len(value)<2:
            aseguir1=value[ind1]
            gen2=True
            genextra=True

        if gen1==True:
            xx1=np.array([[aseguir2[3]+tam_carril*self.lado_inicial,ordp[indice][1][1]]])
        if gen2==True:
            xx=np.array([[aseguir1[3]+tam_carril*self.lado_inicial*-1,ordp[int(aseguir1[0])][1][1]]])
        if genextra==True:
            xx=np.array([[aseguir1[3]+tam_carril*self.lado_inicial*-2,ordp[int(aseguir1[0])][1][1]]])
        
        if gen1==False:
            xx1=np.asarray(ordp[int(aseguir1[0])])
        if gen2==False:
            xx=np.asarray(ordp[int(aseguir2[0])])
        if rside==True:
            b_b=abs(xx1[0][0]-xx[0][0])/2*self.lado_inicial*-1
        else:
            b_b=abs(xx1[0][0]-xx[0][0])/2*self.lado_inicial

            # print(self.ang)
            

            # if(abs(self.ang)>15):
            #     self.contador+=1
            # else:
            #     self.contador=0

            # if(self.contador>5):
            #     xx=np.array([value[ind1][3]+tam_carril*np.sign(self.ang),ordp[indice][1][1]])
            #     xx1=np.asarray(ordp[indice])
            #     kk=0
            #     change=np.sign(self.ang)
            #     #print('no perder carril')



        if len(xx1)>=len(xx):
            line_fol=xx1
        else:
            line_fol=xx
    #########################################################################
    #TERMINAN CAMBIOS PARA ROOOOOSSS


       
       
       
       
       
            
        x_n=np.array([line_fol[:,0]]).T
        y_n=np.array([line_fol[:,1]]).T#[abs(xx1[:,1]-rws[0])]).T
        data =np.hstack( (x_n,y_n) )
        ratio = 0.
        model_m = 0.
        model_c = 0.
        n_samples=len(x_n)
     
    # perform RANSAC iterations
        for it in range(ransac_iterations):
     
            # pick up two random points
            n = 2
            
            all_indices = np.arange(x_n.shape[0])
            np.random.shuffle(all_indices)
            
            indices_1 = all_indices[:n]
            indices_2 = all_indices[n:]
     
            maybe_points = data[indices_1,:]
            test_points = data[indices_2,:]
     
            # find a line model for these points
            m, c,points = find_line_model(maybe_points)
            #print(c)
            x_list = []
            y_list = []
            num = 0
     
            # find orthogonal lines to the model for all testing points
            for ind in range(test_points.shape[0]):
     
                x0 = test_points[ind,0]
                y0 = test_points[ind,1]
     
                # find an intercept point of the model with a normal from point (x0,y0)
                x1, y1 = find_intercept_point(m, c, x0, y0)
                
                # distance from point to the model
                dist = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
                
                # check whether it's an inlier or not
                if dist < ransac_threshold:
                    x_list.append(x0)
                    y_list.append(y0)
                    num += 1
                    
            x_inliers = np.array(x_list)
            y_inliers = np.array(y_list)
     
            # in case a new model is better - cache it
            if num/float(n_samples) > ratio:
                ratio = num/float(n_samples)
                model_m = m
                model_c = c
                x_final=points[1,0]
                y_final=points[1,1]
                theta=np.arctan2(points[1,1]-points[0,1],points[1,0]-points[0,0])       
                theta=theta-np.pi/2
                if np.abs(np.rad2deg(theta))>90:
                    theta=theta+np.pi
                #print('theta',np.rad2deg(theta))
                rho=points[1,0]*np.cos(theta)+points[1,1]*np.sin(theta)
            
            # we are done in case we have enough inliers
            if num > n_samples*ransac_ratio:
              #  print 'The model is found !'
                break

        xmin=0#min(line_fol[:,0])
        xmax=250#max(line_fol[:,0])
        ss=-(np.cos(theta))/(np.sin(theta))
        c=rho/(np.sin(theta))
        if(self.park_flg==True):
            d=((rho+(b_b+20))/np.sin(theta))
        else:
            d=((rho+b_b)/np.sin(theta))   
        cv2.line(warped,(xmin,long(xmin*ss+d)),(xmax,long(xmax*ss+d)),(255,0,0),2)  ##dibujamos line a seguir
       # cv2.line(warped,(int(centro),0),(int(centro),int(rows2)),(255,255,0),2)
        
        ### Seguimiento de linea
        #y_seg=(centro*ss)+d
        #x_seg=(rows2-d)/ss
        y_seg=rows2-50
        x_seg=(y_seg-d)/ss##coordenada x de ransac centro de carril 
        self.ang=np.rad2deg(np.arctan((y_seg-rows2)/(x_seg-centro)))#angulo con respecto a horizontal
        self.ang=(np.abs(self.ang)-90)*np.sign(self.ang)

        #print('angulo=',self.ang)
        cv2.line(warped,(int(centro),int(rows2)),(int(x_seg),int(y_seg)),(255,0,0),2)

        
        #cv2.line(warped,(int(xx1[0][0]),int(rows2)),(int(xx1[0][0]),0),(255,0,0),2)
        #cv2.line(warped,(int(xx[0][0]),int(rows2)),(int(xx[0][0]),0),(255,0,0),2)


        #cv2.circle(warped,(22,80), , (255,255,255),1)
        #cv2.circle(warped,(59,80), 1, (255,255,255),1)
        #self.pub_ang.publish(ang)
        self.pub_ang.publish(self.ang)
        try:
          #self.image_pub.publish(self.bridge.cv2_to_imgmsg(frame, "bgr8"))
          self.image_pub.publish(self.bridge.cv2_to_imgmsg(warped, "mono8"))
        except CvBridgeError as e:
          print(e)

    self.conta += 1

def main(args):
  ic = image_converter()
  rospy.init_node('image_converter', anonymous=True)
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
