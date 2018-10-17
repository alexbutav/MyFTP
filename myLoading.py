import tkinter, time, math
import tkinter.ttk as ttk

class myLoading(tkinter.Toplevel):
    def __init__(self, master = None, width = 250, height = 250, footer_height = 50,
                 animation_update_period = 40, circle_radius = 15, minimal_circle_radius = 5,
                 window_name = "Загрузка", label_initial_text = "Загрузка...",
                 circle_margin = 15, cycle_duration = 5):
        super().__init__(master)
        self._init_constants(animation_update_period, circle_radius, minimal_circle_radius,
                             circle_margin, cycle_duration)
        self._init_ui(window_name, label_initial_text, width, height, footer_height)
        self._start_animation()
        #self.mainloop()

    def _init_constants(self, animation_update_period, circle_radius, minimal_circle_radius,
                        circle_margin, cycle_duration):
        self.circle = None                   #object of moving circle
        self.cycle_duration = cycle_duration #sec
        self.padding = circle_margin         #padding from top
        self.r = circle_radius               #initial moving circle radius
        self.minr = minimal_circle_radius 
        #self.update()                       #for working winfo method
                                             #replaced with self.resizable()
        self.update_period = animation_update_period
    
    def _init_ui(self, window_name, label_initial_text, width, height, footer_height):
        self.title(window_name)
        #centering window
        self.geometry("+%d+%d" % (self.winfo_screenwidth()/2 - width/2,
                                  self.winfo_screenheight()/2 - height/2))
        self.canvas = tkinter.Canvas(self, width = width, height = height - footer_height,
                                     bg="#fff", highlightthickness=0)
        self.canvas.pack()
        self.footer = tkinter.Frame(self, height = footer_height,  bg="#fff")
        self.footer.propagate(0)
        self.footer.pack(fill = tkinter.X)
        self.label = tkinter.Label(self.footer, text = label_initial_text, bg="#fff")
        self.label.pack(fill = tkinter.BOTH, expand = tkinter.YES)
        self.progress = ttk.Progressbar(self.footer, mode="determinate")
        self.progress.pack()

        self.resizable(False, False)

    def _draw_circle(self,x = 125 , y = 100, r = 20, color = "#e0e0e0"):
        return self.canvas.create_oval(x - r, y - r, x + r, y + r, fill = color, width=0)
    
    def _start_animation(self):
        self.start_time = time.time()
        self._update_animation()

    def _update_animation(self):
        timePasted = time.time() - self.start_time
        proc = abs(math.sin( math.pi * timePasted / self.cycle_duration - math.pi/2))
        r = self.minr + self.r*proc
        R = self.canvas.winfo_height()/2 - (self.padding + r)
        fi = math.radians(360*( timePasted / self.cycle_duration ))
        x = self.canvas.winfo_width()/2 + R*math.cos(fi)
        y = self.canvas.winfo_height()/2 + R*math.sin(fi)
        self.canvas.delete(self.circle)
        self.circle = self._draw_circle(x, y, r)
        self.after(self.update_period, self._update_animation)

    def set_progress(self, value):
        self.progress['value'] = value
        
    def set_info(self, info = "Загрузка..."):
        self.label.config(text = info)
        
    def stop_aimation(self):
        self.destroy()
