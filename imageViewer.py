import tkinter, math, threading
from tkinter import filedialog
from PIL.ImageTk import PhotoImage, Image
from ftplib import FTP
import tkinter.ttk as ttk
from io import BytesIO
from PIL import ImageFile
from tkinter import messagebox
from loginParameters import FTP_ACCOUNT #ftp login information !
ImageFile.LOAD_TRUNCATED_IMAGES = True     #чтобы PIL загружал битые файлы, если такие будут

class imageViewer(tkinter.Frame):
    def __init__(self, images_array, thumb_size = (128,128), connection=None, *args, **kwargs):
        tkinter.Frame.__init__(self, *args, **kwargs)
        print(args[0])
        self._init_constants(images_array, thumb_size, connection)
        self._init_gui()
        self._draw_images()

    def _init_constants(self, images_array, thumb_size, connection):
        self._connection = connection
        self._images_array = images_array   #массив словарей вида {"img": оригинальноеИзображение ,"thumb": уменьшенное }
        self._buttons_array = []            #здесь хранятся ссылки на кнопки с фотографиями
        self._button_clicked = None         #массив вида [ссылка на кнопку, которая уже нажата | индекс изображения, которое уже нажато]
        self._vline_width = 20              #px
        self._thumb_size = thumb_size
        self._save_array = []               #массив с индексами фотографий, которые нужно сохранить
        self._images_to_delete = []
        self._canvas_windows = []
        self._footer_height = 50
        
    def _init_gui(self):
        self.config(bg="#fff", height=400)
        self.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=tkinter.YES)
        
        content = tkinter.Frame(self)
        footer = tkinter.Frame(self, height = self._footer_height)
        
        content.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=tkinter.YES)
        footer.pack(side=tkinter.BOTTOM, fill=tkinter.X, expand=tkinter.YES)
        
        self.canvas = tkinter.Canvas(content)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        vscrollBar = tkinter.Scrollbar(content)
        
        vscrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.canvas.pack(fill=tkinter.BOTH, expand=tkinter.YES)
        
        vscrollBar.config(command=self._my_yview)
        self.canvas.config(yscrollcommand=vscrollBar.set)

        self._save_button = tkinter.Button(footer, text="Сохранить изменения", command=self._start_saving, state=tkinter.DISABLED)
        self._save_button.place(relx=0,rely=0.5,anchor=tkinter.W)

        self._progress = ttk.Progressbar(footer, mode="determinate")
        self._progress.place(relx=0.5,rely=0.5,anchor=tkinter.CENTER)

        self._delete_button = tkinter.Button(footer, text="Удалить фотографию", command=self._delete_image, state=tkinter.DISABLED)
        self._delete_button.place(relx=1,rely=0.5,anchor=tkinter.E)
    
    def _draw_images(self):
        del self._buttons_array
        self._buttons_array = []
        Nimages = len(self._images_array)
        Ncols = math.floor(math.sqrt(Nimages))
        Nrows = math.ceil(Nimages/Ncols)

        for row_id in self._canvas_windows:
            self.canvas.delete(row_id)
        
        for rown in range(Nrows):
            row = tkinter.Frame(self.canvas)
            row.pack(fill=tkinter.X)
            for coln, img_dict in enumerate(self._images_array[rown*Ncols:(rown+1)*Ncols]):
                img_index = rown*Ncols + coln
                
                #adding vertical line
                myVline(self, img_index, self._vline_width, row)

                #adding photo button
                btn = tkinter.Button(row, image=img_dict["thumb"], width=self._thumb_size[0], height=self._thumb_size[1])
                self._buttons_array.append(btn)
                btn.config(command=lambda b=btn,i=img_index :self._swap(b,i))
                btn.pack(side=tkinter.LEFT)
                
            #adding lines into canvas
            row_id = self.canvas.create_window(0, rown * self._thumb_size[1],
                                 anchor=tkinter.NW, window=row,
                                 width=(Ncols*self._thumb_size[0]+(Ncols+1)*self._vline_width),
                                 height=self._thumb_size[1])
            self._canvas_windows.append(row_id)
            
        #config scrollregion
        self.canvas.config(width=Ncols*self._thumb_size[0]+(Ncols+1)*self._vline_width,
                           height=600, scrollregion=(0,0,Ncols*self._thumb_size[0]+(Ncols+1)*self._vline_width, (rown+1)*self._thumb_size[1]))
 
    def _swap(self, btn, i):
        if self._button_clicked == None:                       #если выбрана только первая фоотграфия
            self._delete_button.config(state=tkinter.NORMAL)   #разрешить удалять фотографии
            self._button_clicked = (btn, i)
            btn.config(relief=tkinter.SUNKEN)
        else:                                                  #если выбрана вторая
            self._delete_button.config(state=tkinter.DISABLED) #запрещать удалять фотографии
            button_clicked = self._button_clicked[0]
            index_clicked = self._button_clicked[1]
            self._images_array[index_clicked], self._images_array[i] = self._images_array[i], self._images_array[index_clicked]
            button_clicked.config(relief=tkinter.RAISED, image=self._images_array[index_clicked]["thumb"])
            btn.config(image=self._images_array[i]["thumb"])
            self._button_clicked = None
            
        self._check_changes()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*round(event.delta/120), "units")

    def _my_yview(self, *args, **kwargs):
        self.canvas.yview(*args)
        self.update()

    def _check_changes(self):
        save_array = []
        for index, dict in enumerate(self._images_array, 1):
            if index != dict["start_index"]:
                save_array.append(index - 1)
        if len(save_array) == 0:
            if self._save_button["state"] != tkinter.DISABLED:
                self._save_button.config(state=tkinter.DISABLED)
            return False
        else:
            if self._save_button["state"] == tkinter.DISABLED:
                self._save_button.config(state=tkinter.NORMAL)
            self._save_array = save_array
            return True

    def _delete_image(self):
        self._delete_button.config(state=tkinter.DISABLED)
        img_index = self._button_clicked[1]
        self._images_to_delete.append(self._images_array[img_index])
        del self._images_array[img_index]
        self._draw_images()
        self._button_clicked = None
        self._check_changes()
        
    def _upload_images(self, connection):
        for index in self._save_array:
            if self._images_array[index]["start_index"] == 0:
                buff = BytesIO()
                total = buff.getbuffer().nbytes
                self._images_array[index]["img"].save(buff, format="JPEG")                     #
                buff.seek(0)                                                                   #устанавливаем указатель буффера на начало
                
                total = buff.getbuffer().nbytes
                uploaded = 0
                def upd(data):
                    nonlocal uploaded
                    nonlocal total
                    uploaded += len(data)
                    self._progress['value'] = round(uploaded / total * 100, 2)
                
                connection.storbinary("STOR {}.jpg".format(index+1), buff, callback=upd)
                self._progress['value'] = 0
                self._images_array[index]["start_index"] = index + 1

    def _start_saving(self):
        self._upl_thread = threading.Thread(target=self._save_changes)
        self._upl_thread.start()

    def _save_changes(self):
        self._save_button.config(state=tkinter.DISABLED)
        with FTP(host = FTP_ACCOUNT["host"],
                 user = FTP_ACCOUNT["user"],
                 passwd = FTP_ACCOUNT["passwd"]) as connection:
            
            if connection != None:
                connection.cwd("domains")
                connection.cwd("viva-comfort.com")
                connection.cwd("gallery")
                
                img_names = connection.nlst()

                for img_dict in self._images_to_delete:
                    #print("deleting {}.jpg".format(img_dict["start_index"]))
                    connection.delete("{}.jpg".format(img_dict["start_index"]))     
                    img_names.remove("{}.jpg".format(img_dict["start_index"]))
                del self._images_to_delete
                self._images_to_delete = []
                    
                for index in self._save_array:
                    old_name = "{}.jpg".format(self._images_array[index]["start_index"])
                    new_name = "{}.jpg".format(index + 1)
                    if(self._images_array[index]["start_index"] > 0):
                        if old_name != new_name:
                            #если имя, в которое хотим переименовать уже есть
                            if new_name in img_names:
                                connection.rename(new_name, "temp")
                                connection.rename(old_name, new_name)                                
                                connection.rename("temp", old_name)
                                
                                #массив _save_array формируется из условия не соответствия настоящего index + 1 словаря, со значением, которое у этого словаря в "start_index".
                                #на сервере есть файл со значением, которое сейчас соответствует index + 1 словарю, нужно найти элемент в массиве _images_array, у которого значене
                                #"start_index" соответствует index + 1 и поменять его на "start_index" нашей фотографии, чьё имя мы хотим поменять
                                #что здесь и делается
                                next( dict for dict in  self._images_array if dict["start_index"] == index + 1)["start_index"] = self._images_array[index]["start_index"]
                                
                                self._images_array[index]["start_index"] = index + 1                      
                            else:
                                connection.rename(old_name, new_name)
                                img_names.append(new_name) #добавляем новоё имя в массив с именами, полученный с сервера
                                img_names.remove(old_name)
                                self._images_array[index]["start_index"] = index + 1

                self._upload_images(connection)
                self._check_changes()
                messagebox.showinfo("Загрузка завершена", "Изменения сохранены.")
                

class myVline(tkinter.Frame):
    def __init__(self, image_viewer, index, width, *args, **kwargs):
        tkinter.Frame.__init__(self, width=width, *args, **kwargs)
        self.propagate(0)
        self.pack(side=tkinter.LEFT, fill=tkinter.Y)
        self.index = index
        self.image_viewer = image_viewer
        self._init_constants()
        
        pasteButton = tkinter.Button(self, command=self._line_clicked, bg="#FFF")
        pasteButton.bind("<Enter>", self.on_mouseover)
        pasteButton.bind("<Leave>", self.on_mouseout)
        pasteButton.bind("<ButtonRelease-1>", self.on_mouserelease)
        pasteButton.config(bd=0, activebackground="white")
        pasteButton.pack(fill=tkinter.BOTH, expand=1)
    
    def _line_clicked(self):
        firstButton = self.image_viewer._button_clicked
        
        if firstButton != None:
            indexFrom = firstButton[1]
            indexTo = self.index
            Buttons = self.image_viewer._buttons_array
            Images = self.image_viewer._images_array
            buff = Images[indexFrom]
            if indexTo > indexFrom and indexTo - indexFrom > 1:
                for add in range(indexTo - indexFrom - 1):
                    Images[indexFrom + add] = Images[indexFrom + add + 1]
                    Buttons[indexFrom + add].config(image=Images[indexFrom + add]["thumb"])
                Images[indexTo - 1] = buff
                Buttons[indexTo - 1].config(image=Images[indexTo - 1]["thumb"])
            elif indexTo < indexFrom and indexFrom - indexTo >= 1:
                for add in range(indexFrom - indexTo):
                    Images[indexFrom - add] = Images[indexFrom - add - 1]
                    Buttons[indexFrom - add].config(image=Images[indexFrom - add]["thumb"])
                Images[indexTo] = buff
                Buttons[indexTo].config(image=Images[indexTo]["thumb"])
            Buttons[indexFrom].config(relief=tkinter.RAISED)
            self.image_viewer._delete_button.config(state=tkinter.DISABLED)
            self.image_viewer._button_clicked = None
        else:
            filename =  filedialog.askopenfilename(initialdir = "/",
                                                   title = "Выберите файл",
                                                   filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
            if filename != "":
                imgObj = Image.open(filename)
                imageCopy = imgObj.copy()
                imageCopy.thumbnail( self.image_viewer._thumb_size, Image.ANTIALIAS )
                thumbnail = PhotoImage(imageCopy)
                imgDict = {"img":imgObj, "thumb":thumbnail, "start_index":0}
                self.image_viewer._images_array.insert(self.index, imgDict)
                self.image_viewer._draw_images()
            
        self.image_viewer._check_changes()

    def _init_constants(self):
        self.onover_color = "#4444DD"
        self.onout_color = "#FFFFFF"
        self.onrelease_color = "#FFFFFF"


    def on_mouseover(self, event):
        event.widget.config(bg=self.onover_color)

    def on_mouseout(self, event):
        event.widget.config(bg=self.onout_color)
                                
    def on_mouserelease(self, event):
        event.widget.config(bg=self.onrelease_color)

    


















        
        
