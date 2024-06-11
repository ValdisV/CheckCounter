import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tk_filedialog
import tkinter.messagebox as tk_messagebox
import tkinterdnd2 as tk_dnd
import os
import PyPDF2
import traceback as tb


APP_NAME = "Money Generator $$$"
__author__ = "ValdisV"
__version__ = "1.1.0"


def get_num_sum(old_sum, tag):
    match tag:
        case 1:
            return old_sum
        case 0:
            return round(old_sum / 2)
        case -1:
            return 0


def to_whole_int(text:str):
    return int(text.replace(",", ""))


def float_to_string(value:str):
    part1, part2 = str(value).split(".")
    return f"{part1}.{part2.ljust(2, '0')}"


def int_to_float_str(value:str, start=""):
    if value is None: return ""
    return f"{start}{float_to_string(value / 100)}"


def get_procent(value, total):
    return round((value / total) * 100)


def get_maxima_check_data(file_path:str):
    with open(file_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        check = pdf_reader.pages[0].extract_text()
    
    product_check = check[check.find("Čeks "): check.find("====")].split("\n")[1: -1]
    products = {}
    next_deposite = False
    prev_product = None
    product_total_cost = 0
    prev_new = False

    for product in product_check:
        if product == "Papildus depozīta maksa":
            next_deposite = True
            continue

        elif product.startswith("Atlaide: "):
            total_cost = to_whole_int(product[product.find("("): product.find(")")].split(" ")[-1])
            discount = product[product.find("-") + 2:]
            discount = to_whole_int(discount[: discount.find(" ")])

            product_total_cost -= discount
            products[prev_product]["total_cost"] = total_cost
            products[prev_product]["discount"] = discount

        elif product.startswith("  "):  # gets cost, quantity, total cost and deposite cost

            if prev_new:  # adds product to products list
                if prev_product in products:
                    num = 2
                    while f"({num}) {prev_product}" in products: num += 1
                    prev_product = f"({num}) {prev_product}"

                products[prev_product] = {"tag": 0}
                prev_new = False

            text = product.replace(" ", "")
            sep2 = len(text) - 5  # separates quantity from total cost
            while text[sep2 - 1].isnumeric(): sep2 -= 1
            total_cost = to_whole_int(text[sep2: -1])

            product_total_cost += total_cost
            if next_deposite:
                products[prev_product]["deposite"] = total_cost
                next_deposite = False
            else:
                sep1 = text.find("X") # separates cost from quantity
                cost = to_whole_int(text[: sep1])
                quantity = text[sep1 + 1: sep2]

                products[prev_product]["total_cost"] = total_cost
                products[prev_product]["cost"] = cost
                products[prev_product]["quantity"] = quantity

        elif prev_new:  # product title is in multiple lines
            prev_product += " " + product

        else:  # new product
            prev_product = product
            prev_new = True

    return product_total_cost, products


class App(tk_dnd.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - | v.{__version__} | - | Created by: {__author__} |")

        self.style = ttk.Style(self)
        self.style.configure("Treeview", rowheight=25)
        self.style.map("Treeview", background=[("selected", "#009DA1")])

        # all checks
        self.all_checks = {}
        self.all_check_data = {}
        self.final_cost = self.total_cost = 0

        # currently selected check
        self.current_file = None
        self.check_data = {}  # check: {old_sum, new_sum, tag}
        self.check_products = {}

        self.show_home_layout()

    def show_home_layout(self):
        # ---- MAIN FRAME ----
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=1, padx=(5, 5))

        # ---- FILE FRAME ----
        self.file_frame = ttk.LabelFrame(self.main_frame, text="MAXIMA - checks:")
        self.file_frame.pack(side="left", fill="y")

        # -- UP BUTTON FRAME --
        self.file_up_btn_frame = ttk.Frame(self.file_frame)
        self.file_up_btn_frame.pack(fill="x", pady=(3, 3))

        self.add_file_btn = ttk.Button(self.file_up_btn_frame, text="Add", command=self.add_files)
        self.add_file_btn.pack(side="left", padx=(3, 0))
        self.open_file_btn = ttk.Button(self.file_up_btn_frame, text="Open", command=self.open_file)
        self.open_file_btn.pack(side="left", padx=(3, 0))
        self.remove_file_btn = ttk.Button(self.file_up_btn_frame, text="Remove", command=self.remove_file)
        self.remove_file_btn.pack(side="left", padx=(3, 0))
        self.deselect_file_btn = ttk.Button(self.file_up_btn_frame, text="De-select", command=self.deselect_file)
        self.deselect_file_btn.pack(side="left", padx=(3, 0))

        # -- TREE FRAME --
        self.file_tree_frame = ttk.Frame(self.file_frame)
        self.file_tree_frame.pack(fill="y", expand=1)

        self.file_tree = ttk.Treeview(self.file_tree_frame, selectmode="browse", columns=("cost", "procent", "total_cost"))
        self.file_tree.bind("<<TreeviewSelect>>", self.file_selected)
        self.file_tree.drop_target_register(tk_dnd.DND_FILES)
        self.file_tree.dnd_bind('<<Drop>>', self.add_files)

        self.file_tree.heading("#0", text="Name")
        self.file_tree.heading("cost", text="Cost")
        self.file_tree.heading("procent", text="Return")
        self.file_tree.heading("total_cost", text="Full price")

        self.file_tree.column("#0", width=200)
        self.file_tree.column("cost", anchor="center", stretch=False, width=60)
        self.file_tree.column("procent", anchor="center", stretch=False, width=60)
        self.file_tree.column("total_cost", anchor="center", stretch=False, width=60)

        self.file_tree.tag_configure(1, background="#ABFF6C")  # full price
        self.file_tree.tag_configure(0, background="#FFBA6C")  # half price
        self.file_tree.tag_configure(-1, background="#FF6C6C")  # remove price

        self.file_tree.pack(side="left", fill="y", expand=1)

        self.file_y_scrollbar = ttk.Scrollbar(self.file_tree_frame, command=self.file_tree.yview)
        self.file_tree.config(yscrollcommand=self.file_y_scrollbar.set)
        self.file_y_scrollbar.pack(side="left", fill="y")

        # ---- PRODUCT FRAME ----
        self.product_frame = ttk.LabelFrame(self.main_frame, text="Prducts:")
        self.product_frame.pack(side="left", fill="both", expand=1, padx=(5, 0))

        # -- UP BUTTON FRAME --
        self.product_up_btn_frame = ttk.Frame(self.product_frame)
        self.product_up_btn_frame.pack(fill="x", pady=(3, 3))

        self.full_price_btn = ttk.Button(self.product_up_btn_frame, text="Full (q)", command=self.product_to_full_price)
        self.full_price_btn.pack(side="left", padx=(3, 0))
        self.half_price_btn = ttk.Button(self.product_up_btn_frame, text="Half (a)", command=self.product_to_half_price)
        self.half_price_btn.pack(side="left", padx=(3, 0))
        self.remove_price_btn = ttk.Button(self.product_up_btn_frame, text="Remove (z)", command=self.product_to_remove_price)
        self.remove_price_btn.pack(side="left", padx=(3, 0))

        # -- TREE FRAME --
        self.product_tree_frame = ttk.Frame(self.product_frame)
        self.product_tree_frame.pack(fill="both", expand=1)

        self.product_tree = ttk.Treeview(self.product_tree_frame, selectmode="browse", columns=("cost", "total_cost", "count", "deposits", "discount"))

        self.product_tree.heading("#0", text="Product")
        self.product_tree.heading("cost", text="Cost")
        self.product_tree.heading("total_cost", text="Full price")
        self.product_tree.heading("count", text="Count")
        self.product_tree.heading("discount", text="Discount")
        self.product_tree.heading("deposits", text="Deposits")

        self.product_tree.column("#0", width=400)
        self.product_tree.column("cost", anchor="center", stretch=False, width=60)
        self.product_tree.column("total_cost", anchor="center", stretch=False, width=60)
        self.product_tree.column("count", anchor="center", stretch=False, width=100)
        self.product_tree.column("discount", anchor="center", stretch=False, width=60)
        self.product_tree.column("deposits", anchor="center", stretch=False, width=60)

        self.product_tree.tag_configure(1, background="#ABFF6C")  # full price
        self.product_tree.tag_configure(0, background="#FFBA6C")  # half price
        self.product_tree.tag_configure(-1, background="#FF6C6C")  # remove price

        self.product_tree.bind("<q>", self.product_to_full_price)
        self.product_tree.bind("<a>", self.product_to_half_price)
        self.product_tree.bind("<z>", self.product_to_remove_price)

        self.product_tree.pack(side="left", fill="both", expand=1)

        self.product_y_scrollbar = ttk.Scrollbar(self.product_tree_frame, command=self.product_tree.yview)
        self.product_tree.config(yscrollcommand=self.product_y_scrollbar.set)
        self.product_y_scrollbar.pack(side="left", fill="y")

        # ---- TOTAL COST FRAME ----
        self.total_cost_frame = ttk.Frame(self)
        self.total_cost_frame.pack(side="bottom", anchor="s", pady=(5, 5))

        self.final_cost_label = tk.Label(self.total_cost_frame, text="「 ✦ Nyaaaaaaaaaa ✦ 」", font=("Arial", 20))
        self.final_cost_label.pack(side="left")
        self.total_cost_label = tk.Label(self.total_cost_frame, font=("Arial", 20))
        self.total_cost_label.pack(side="left")
        self.profit_label = tk.Label(self.total_cost_frame, font=("Arial", 20))
        self.profit_label.pack(side="left", padx=(5, 0))

    # ADD, REMOVE, SELECT FILES ----------------------------------------------
    def add_files(self, event=None):
        if event is None:
            files = tk_filedialog.askopenfilenames(title="Select checks", filetypes=[("MAXIMA checks", ".pdf")])
        else:  # draged in files
            files = (path for path in self.tk.splitlist(event.data) if os.path.splitext(path)[1] == ".pdf")
        
        if not files: return
        for file_ in files:
            if file_ in self.all_checks: continue
            
            try:
                total_cost, products = get_maxima_check_data(file_)
                new_cost = get_num_sum(total_cost, 0)
                procent = get_procent(new_cost, total_cost)
            except Exception as exc:
                print(f" ERROR! - {file_} ".center(100, "-"))
                print(tb.format_exc())
                print()
                tk_messagebox.showerror("Error!", f"Failed to load check!\n'{file_}'")
                continue

            self.file_tree.insert("", "end", file_, text=os.path.basename(file_), tags=[0], values=(
                int_to_float_str(new_cost),
                f"{procent}%",
                int_to_float_str(total_cost)
            ))
            
            self.final_cost += new_cost
            self.total_cost += total_cost
            self.all_check_data[file_] = {"old_cost": total_cost, "new_cost": new_cost}
            self.all_checks[file_] = products
        
        self.update_total_cost_data()
        self.total_cost_label.config(text=f" / Total: {int_to_float_str(self.total_cost)} EUR]")

    def remove_file(self):
        files = self.file_tree.selection()
        if not files: return
        file_ = files[0]
        
        self.final_cost -= self.check_data["new_cost"]
        self.total_cost -= self.check_data["old_cost"]
        del self.all_checks[file_]
        del self.all_check_data[file_]

        self.clear_product_tree()
        self.file_tree.delete(*files)
        self.update_total_cost_data()
        self.total_cost_label.config(text=f" / Total: {int_to_float_str(self.total_cost)} EUR]")

    def file_selected(self, _=None):
        files = self.file_tree.selection()
        if not files: return

        self.current_file = files[0]
        self.check_data = self.all_check_data[self.current_file]
        self.check_products = self.all_checks[self.current_file]
        self.refresh_product_tree()

    def deselect_file(self):
        self.file_tree.selection_remove(self.file_tree.selection())
        self.clear_product_tree()

    def open_file(self):
        files = self.file_tree.selection()
        if files: os.startfile(files[0])

    # UPDATE PRODUCT TAG ----------------------------------------------------------
    def change_product_tags(self, tag:int, index):
        products = self.product_tree.selection()
        if not products: return
        product = products[0]

        item = self.product_tree.item(product)
        old_tag = item["tags"][0]
        if old_tag == tag: return

        offset = old_tag > tag
        product_data = self.check_products[product]

        self.product_tree.move(product, "", index - offset)
        self.product_tree.item(product, tags=[tag], values=(int_to_float_str(get_num_sum(product_data["total_cost"], tag)), *item["values"][1:]))
        product_data["tag"] = tag

        self.product_tree.selection_remove(*products)

        new_sum = 0
        for product, data in self.check_products.items():
            new_sum += get_num_sum(data["total_cost"] + data.get("deposite", 0), data["tag"])

        file_item = self.file_tree.item(self.current_file)
        procents = get_procent(new_sum, self.check_data['old_cost'])
        tag = -1 if procents < 48 else 1 if procents > 52 else 0

        self.file_tree.item(self.current_file, tags=[tag], values=(int_to_float_str(new_sum), f"{procents}%", *file_item["values"][2:]))
        self.final_cost += new_sum - self.check_data["new_cost"] 
        self.check_data["new_cost"] = new_sum
        self.update_total_cost_data()

    def product_to_full_price(self, _=None):
        self.change_product_tags(1, 0)

    def product_to_half_price(self, _=None):
        tags = self.get_product_tags()
        self.change_product_tags(0, tags.count(1))

    def product_to_remove_price(self, _=None):
        tags = self.get_product_tags()
        self.change_product_tags(-1, tags.count(0) + tags.count(1))

    def get_product_tags(self):
        return [data["tag"] for data in self.check_products.values()]
    
    # OTHER -------------------------------------------------------------------
    def refresh_product_tree(self):
        self.product_tree.delete(*self.product_tree.get_children())

        for product, data in dict(sorted(self.check_products.items(), key=lambda data_: data_[1]["tag"], reverse=True)).items():
            tag = data.get("tag")
            total_cost = data.get("total_cost")

            self.product_tree.insert("", "end", product, text=product, tags=[tag], values=(
                int_to_float_str(get_num_sum(total_cost, tag)),
                int_to_float_str(total_cost),
                data.get("quantity"),
                int_to_float_str(data.get("deposite"), "+"),
                int_to_float_str(data.get("discount"), "-")
            ))

    def update_total_cost_data(self):
        self.final_cost_label.config(text=f"[Return: {int_to_float_str(self.final_cost)}")
        if self.total_cost != 0:
            procents = get_procent(self.final_cost, self.total_cost)
            color = "red" if procents < 48 else "green" if procents > 52 else "orange"
            self.profit_label.config(text=f"[{procents}%]", foreground=color)
        else:
            self.profit_label.config(text="[HEHE%]")

    def clear_product_tree(self):
        self.product_tree.delete(*self.product_tree.get_children())
        self.current_file = None
        self.check_data = {}
        self.check_products = {}


if __name__ == "__main__":
    app = App()
    app.mainloop()
