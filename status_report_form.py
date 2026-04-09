from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from generate_status_report import build_data_from_simple_projects, build_deck


class StatusReportForm:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Status Report Form")
        self.root.geometry("900x620")
        self.projects: list[dict[str, str]] = []

        self.title_var = tk.StringVar(value="Project Status Report")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%d %B %Y"))
        self.rag_var = tk.StringVar(value="Auto")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Report title").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.title_var, width=60).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        ttk.Label(frame, text="Report date").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Entry(frame, textvariable=self.date_var, width=22).grid(row=1, column=2, sticky="w", padx=(10, 0), pady=(2, 10))

        ttk.Label(frame, text="Project name").grid(row=2, column=0, sticky="w")
        self.project_name_entry = ttk.Entry(frame, width=38)
        self.project_name_entry.grid(row=3, column=0, sticky="ew", pady=(2, 8))

        ttk.Label(frame, text="Project status").grid(row=2, column=1, columnspan=2, sticky="w", padx=(10, 0))
        self.status_text = tk.Text(frame, height=4, width=58, wrap="word")
        self.status_text.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(2, 8))

        ttk.Label(frame, text="RAG (optional)").grid(row=4, column=0, sticky="w")
        rag_selector = ttk.Combobox(
            frame,
            textvariable=self.rag_var,
            values=["Auto", "Green", "Amber", "Red"],
            state="readonly",
            width=12,
        )
        rag_selector.grid(row=4, column=0, sticky="w", pady=(2, 8))

        button_row = ttk.Frame(frame)
        button_row.grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 10), padx=(10, 0))
        ttk.Button(button_row, text="Add project", command=self.add_project).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(button_row, text="Clear input", command=self.clear_input).pack(side=tk.LEFT, padx=(8, 0))

        columns = ("name", "rag", "status")
        self.project_table = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        self.project_table.heading("name", text="Project")
        self.project_table.heading("rag", text="RAG")
        self.project_table.heading("status", text="Status")
        self.project_table.column("name", width=220, anchor="w")
        self.project_table.column("rag", width=90, anchor="center")
        self.project_table.column("status", width=510, anchor="w")
        self.project_table.grid(row=5, column=0, columnspan=3, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.project_table.yview)
        self.project_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=5, column=3, sticky="ns")

        generate_button = ttk.Button(frame, text="Generate PowerPoint", command=self.generate_presentation)
        generate_button.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(14, 0))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(5, weight=1)

    def add_project(self) -> None:
        name = self.project_name_entry.get().strip()
        status = self.status_text.get("1.0", tk.END).strip()
        selected_rag = self.rag_var.get().strip().lower()

        if not name:
            messagebox.showerror("Missing project name", "Enter a project name before adding.")
            return
        if not status:
            messagebox.showerror("Missing project status", "Enter a project status before adding.")
            return

        if selected_rag not in {"auto", "green", "amber", "red"}:
            messagebox.showerror("Invalid RAG", "Select Auto, Green, Amber, or Red.")
            return

        project = {"name": name, "status": status}
        if selected_rag != "auto":
            project["rag"] = selected_rag

        self.projects.append(project)
        self.project_table.insert("", tk.END, values=(name, selected_rag.upper(), status))
        self.clear_input()

    def remove_selected(self) -> None:
        selected = self.project_table.selection()
        if not selected:
            return

        indices = sorted((self.project_table.index(item_id) for item_id in selected), reverse=True)
        for index in indices:
            self.projects.pop(index)

        for item_id in selected:
            self.project_table.delete(item_id)

    def clear_input(self) -> None:
        self.project_name_entry.delete(0, tk.END)
        self.status_text.delete("1.0", tk.END)
        self.rag_var.set("Auto")

    def generate_presentation(self) -> None:
        if not self.projects:
            messagebox.showerror("No projects", "Add at least one project before generating the report.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save status report",
            defaultextension=".pptx",
            filetypes=[("PowerPoint", "*.pptx")],
            initialfile=f"status-report-{datetime.now().date().isoformat()}.pptx",
        )
        if not output_path:
            return

        data = build_data_from_simple_projects(
            self.projects,
            report_title=self.title_var.get().strip() or "Project Status Report",
            report_date=self.date_var.get().strip() or datetime.now().strftime("%d %B %Y"),
        )
        build_deck(data, Path(output_path).resolve())

        messagebox.showinfo("Done", f"Presentation created:\n{output_path}")



def main() -> None:
    root = tk.Tk()
    StatusReportForm(root)
    root.mainloop()


if __name__ == "__main__":
    main()

