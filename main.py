from ftplib import FTP
from PIL.ImageTk import PhotoImage, Image
from tkinter import Tk, Label
from io import BytesIO
from tkinter import messagebox
from loginParameters import FTP_ACCOUNT #ftp login information !
import tkinter, threading, myLoading, time, math, imageViewer, os, ftplib, sys

class MyFtp(tkinter.Tk):
    def __init__(self,mode="test", *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        self._init_constants(mode)
        self.protocol("WM_DELETE_WINDOW", self._closing) 
        self.mainloop()
    
            
    def _closing(self):
        if self._image_viewer._check_changes() == False:
                self.destroy()
        else:
            if messagebox.askokcancel("Выход", "Есть несохраненные изменения, Вы уверен, что хотите выйти?"):
                self.destroy()
        
       

    def _load_images(self):
        try:
            with FTP(host = FTP_ACCOUNT["host"],
                     user = FTP_ACCOUNT["user"],
                     passwd = FTP_ACCOUNT["passwd"]) as self.connection:
                self.connection.cwd("domains")
                self.connection.cwd("viva-comfort.com")
                self.connection.cwd("gallery")

                if self._mode == "test":
                    img_array = os.listdir("images")
                    img_array = sorted(img_array, key=lambda img: int(img.split(".")[0]))
                    images_number = len(img_array)
                    for index, imgName in enumerate(img_array, 1):
                        imgObj = Image.open(os.path.join("images",imgName))
                        imageCopy = imgObj.copy()
                        imageCopy.thumbnail( self.thumbnail_size, Image.ANTIALIAS )
                        thumbnail = PhotoImage(imageCopy)
                        
                        self.loading.set_progress(round(index / images_number * 100, 2))
                        self.loading.set_info("Загружено %s фото из %s" % (index, images_number))
                        imgName = {"img":imgObj, "thumb":thumbnail, "start_index":index}
                                            
                        self.img_array.append(imgName)
                elif self._mode == "work":
                    img_array = [image[0] for image in self.connection.mlsd() if image[0] != "." and image[0] != ".."]                    
                    img_array = sorted(img_array, key=lambda img: int(img.split(".")[0]))
                    
                    self.total = 0
                    self.downloaded = 0
                    self.connection.sendcmd("TYPE i")    # Switch to Binary mode
                    #calculcating total byte size of images
                    for img in img_array:
                        self.total += self.connection.size(img)
                    self.connection.sendcmd("TYPE A")    # Switch back to ASCII mode            
                    
                    images_number = len(img_array)

                    #images loading
                    for index, imgName in enumerate(img_array, 1):
                        buff = BytesIO()
                        #progressbar function that recive loaded data and changes progressbar
                        def wrt(data):
                            self.downloaded += buff.write(data)
                            self.loading.set_progress(round(self.downloaded / self.total * 100, 2))

                        self.connection.retrbinary("RETR "+imgName, wrt, 8*1024)
                        
                        self.loading.set_info("Загружено %s фото из %s" % (index, images_number))
                        
                        imgObj = Image.open(buff)
                        imageCopy = imgObj.copy()
                        imageCopy.thumbnail( self.thumbnail_size, Image.ANTIALIAS )
                        thumbnail = PhotoImage(imageCopy)
                        
                        imgName = {"img":imgObj, "thumb":thumbnail, "start_index":index}
                        self.img_array.append(imgName)
            self.connection.close()
            self.loading.set_info("Загрузка завершена !")
            self.loading.after(500,self.loading.stop_aimation)
            self.show_window()
        except IOError :
            del self.img_array
            self.img_array = []
            messagebox.showinfo("Сообщение об ошибке", "ошибка подключения, пытаемся снова.")
            self._load_images()

    def _init_constants(self, mode):
        self._image_viewer = 0
        self.withdraw()#hiding root window
        self._mode = mode
        self.img_array = []
        self.thumbnail_size = (128,128)
        self.loading = myLoading.myLoading(self)
        self.l = threading.Thread(target=self._load_images)
        self.l.start()
        return
    
    def show_window(self):
        self._image_viewer = imageViewer.imageViewer(self.img_array, self.thumbnail_size, self.connection, self)
        self.deiconify()
        return

if __name__ == '__main__':
    window = MyFtp("work")
