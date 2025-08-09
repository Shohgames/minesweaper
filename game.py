import tkinter as tk
from tkinter import messagebox
import random
import time

class Cell(tk.Button):
    def __init__(self, master, x, y, click_left, click_right):
        super().__init__(master, width=2, height=1, font=("Helvetica", 14), relief=tk.RAISED)
        self.x = x
        self.y = y
        self.is_mine = False
        self.adjacent = 0
        self.revealed = False
        self.flagged = False
        self.click_left = click_left
        self.click_right = click_right
        self.bind("<Button-1>", self.on_left)
        self.bind("<Button-3>", self.on_right)

    def on_left(self, event):
        self.click_left(self.x, self.y)

    def on_right(self, event):
        self.click_right(self.x, self.y)

    def reveal(self):
        if self.revealed:
            return
        self.revealed = True
        self.config(relief=tk.SUNKEN)
        if self.is_mine:
            self.config(text="*", disabledforeground='red')
        elif self.adjacent > 0:
            self.config(text=str(self.adjacent), disabledforeground=self._num_color())
        self.config(state=tk.DISABLED)

    def toggle_flag(self):
        if self.revealed:
            return
        self.flagged = not self.flagged
        self.config(text=("🚩" if self.flagged else ""))

    def _num_color(self):
        colors = {1:'#0000FF', 2:'#008200', 3:'#FF0000', 4:'#000084', 5:'#840000', 6:'#008284', 7:'#000000', 8:'#808080'}
        return colors.get(self.adjacent, '#000000')

class MinesweeperApp:
    def __init__(self, master, rows=9, cols=9, mines=10):
        self.master = master
        self.rows = rows
        self.cols = cols
        self.total_mines = mines
        self.first_click = True
        self.start_time = None
        self.timer_id = None
        self.running = True

        master.title('Minesweeper')

        top = tk.Frame(master)
        top.pack(padx=6, pady=6)

        self.mine_label = tk.Label(top, text=f'Mines: {self.total_mines}')
        self.mine_label.pack(side=tk.LEFT, padx=6)

        self.time_label = tk.Label(top, text='Time: 0')
        self.time_label.pack(side=tk.LEFT, padx=6)

        restart_btn = tk.Button(top, text='Restart', command=self.restart)
        restart_btn.pack(side=tk.LEFT, padx=6)

        settings_btn = tk.Button(top, text='Settings', command=self.open_settings)
        settings_btn.pack(side=tk.LEFT, padx=6)

        self.board_frame = tk.Frame(master)
        self.board_frame.pack(padx=6, pady=6)

        self.cells = []
        self._build_board()
        self._place_mines_random()
        self._compute_adjacency()

    def _build_board(self):
        for x in range(self.rows):
            row = []
            for y in range(self.cols):
                c = Cell(self.board_frame, x, y, self.on_left_click, self.on_right_click)
                c.grid(row=x, column=y)
                row.append(c)
            self.cells.append(row)

    def _place_mines_random(self):
        # place mines randomly. We'll allow re-shuffle on restart/settings
        coords = [(x, y) for x in range(self.rows) for y in range(self.cols)]
        mines = random.sample(coords, self.total_mines)
        for (x, y) in mines:
            self.cells[x][y].is_mine = True

    def _compute_adjacency(self):
        for x in range(self.rows):
            for y in range(self.cols):
                if self.cells[x][y].is_mine:
                    continue
                count = 0
                for nx in range(x-1, x+2):
                    for ny in range(y-1, y+2):
                        if 0 <= nx < self.rows and 0 <= ny < self.cols:
                            if self.cells[nx][ny].is_mine:
                                count += 1
                self.cells[x][y].adjacent = count

    def on_left_click(self, x, y):
        if not self.running:
            return
        cell = self.cells[x][y]
        if cell.flagged or cell.revealed:
            return
        if self.first_click:
            # ensure first click is never a mine
            if cell.is_mine:
                self._relocate_mine(x, y)
                self._compute_adjacency()
            self.first_click = False
            self.start_timer()

        if cell.is_mine:
            cell.reveal()
            self.game_over(False)
            return

        self._flood_reveal(x, y)
        if self._check_win():
            self.game_over(True)

    def on_right_click(self, x, y):
        if not self.running:
            return
        cell = self.cells[x][y]
        cell.toggle_flag()
        self._update_mine_label()

    def _update_mine_label(self):
        flags = sum(1 for row in self.cells for c in row if c.flagged)
        self.mine_label.config(text=f'Mines: {self.total_mines - flags}')

    def _relocate_mine(self, x, y):
        # move mine at x,y to a random non-mine cell
        self.cells[x][y].is_mine = False
        free = [(i,j) for i in range(self.rows) for j in range(self.cols) if not self.cells[i][j].is_mine and (i,j)!=(x,y)]
        new = random.choice(free)
        self.cells[new[0]][new[1]].is_mine = True

    def _flood_reveal(self, x, y):
        stack = [(x,y)]
        visited = set()
        while stack:
            cx, cy = stack.pop()
            if (cx,cy) in visited:
                continue
            visited.add((cx,cy))
            cell = self.cells[cx][cy]
            if cell.revealed or cell.flagged:
                continue
            cell.reveal()
            if cell.adjacent == 0:
                for nx in range(cx-1, cx+2):
                    for ny in range(cy-1, cy+2):
                        if 0 <= nx < self.rows and 0 <= ny < self.cols:
                            if (nx,ny) not in visited:
                                stack.append((nx,ny))

    def _check_win(self):
        for row in self.cells:
            for c in row:
                if not c.is_mine and not c.revealed:
                    return False
        return True

    def game_over(self, won):
        self.running = False
        self.stop_timer()
        # reveal all mines
        for row in self.cells:
            for c in row:
                if c.is_mine and not c.flagged:
                    c.reveal()
        if won:
            elapsed = int(time.time() - self.start_time) if self.start_time else 0
            messagebox.showinfo('You win', f'You cleared the board in {elapsed} seconds.')
        else:
            messagebox.showinfo('Game over', 'You clicked a mine.')

    def start_timer(self):
        self.start_time = time.time()
        self._tick()

    def _tick(self):
        if not self.running or not self.start_time:
            return
        elapsed = int(time.time() - self.start_time)
        self.time_label.config(text=f'Time: {elapsed}')
        self.timer_id = self.master.after(1000, self._tick)

    def stop_timer(self):
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

    def restart(self):
        self.stop_timer()
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        self.cells = []
        self.first_click = True
        self.start_time = None
        self.timer_id = None
        self.running = True
        self._build_board()
        self._place_mines_random()
        self._compute_adjacency()
        self._update_mine_label()
        self.time_label.config(text='Time: 0')

    def open_settings(self):
        # simple settings dialog
        dlg = tk.Toplevel(self.master)
        dlg.title('Settings')

        tk.Label(dlg, text='Rows').grid(row=0, column=0, padx=6, pady=6)
        rows_var = tk.IntVar(value=self.rows)
        tk.Entry(dlg, textvariable=rows_var).grid(row=0, column=1)

        tk.Label(dlg, text='Cols').grid(row=1, column=0, padx=6, pady=6)
        cols_var = tk.IntVar(value=self.cols)
        tk.Entry(dlg, textvariable=cols_var).grid(row=1, column=1)

        tk.Label(dlg, text='Mines').grid(row=2, column=0, padx=6, pady=6)
        mines_var = tk.IntVar(value=self.total_mines)
        tk.Entry(dlg, textvariable=mines_var).grid(row=2, column=1)

        def apply_settings():
            r = rows_var.get()
            c = cols_var.get()
            m = mines_var.get()
            if r < 5 or c < 5 or m < 1 or m >= r*c:
                messagebox.showerror('Invalid', 'Invalid settings. Ensure 5<=rows,5<=cols and 1<=mines<rows*cols')
                return
            self.rows = r
            self.cols = c
            self.total_mines = m
            dlg.destroy()
            self.restart()

        tk.Button(dlg, text='Apply', command=apply_settings).grid(row=3, column=0, columnspan=2, pady=8)

if __name__ == '__main__':
    root = tk.Tk()
    app = MinesweeperApp(root, rows=9, cols=9, mines=10)
    root.mainloop()
