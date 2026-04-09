from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from analyse_projects import DEFAULT_MODEL, check_ollama_available
from generate_status_report import build_data_from_simple_projects, build_deck


class StatusReportForm:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Status Report Form")
        self.root.geometry("900x700")
        self.projects: list[dict[str, str]] = []

        self.title_var = tk.StringVar(value="Project Status Report")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%d %B %Y"))
        self.rag_var = tk.StringVar(value="Auto")
        self.use_llm_var = tk.BooleanVar(value=False)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        # Report title / date
        ttk.Label(frame, text="Report title").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.title_var, width=60).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 10))
        ttk.Label(frame, text="Report date").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Entry(frame, textvariable=self.date_var, width=22).grid(row=1, column=2, sticky="w", padx=(10, 0), pady=(2, 10))

        # Project entry row
        ttk.Label(frame, text="Project name").grid(row=2, column=0, sticky="w")
        self.project_name_entry = ttk.Entry(frame, width=38)
        self.project_name_entry.grid(row=3, column=0, sticky="ew", pady=(2, 8))
        ttk.Label(frame, text="Project status").grid(row=2, column=1, columnspan=2, sticky="w", padx=(10, 0))
        self.status_text = tk.Text(frame, height=4, width=58, wrap="word")
        self.status_text.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(2, 8))

        # RAG selector
        ttk.Label(frame, text="RAG (optional)").grid(row=4, column=0, sticky="w")
        rag_selector = ttk.Combobox(
            frame, textvariable=self.rag_var,
            values=["Auto", "Green", "Amber", "Red"],
            state="readonly", width=12,
        )
        rag_selector.grid(row=4, column=0, sticky="w", pady=(2, 8))

        # Add / Remove / Clear buttons
        button_row = ttk.Frame(frame)
        button_row.grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 10), padx=(10, 0))
        ttk.Button(button_row, text="Add project", command=self.add_project).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(button_row, text="Clear input", command=self.clear_input).pack(side=tk.LEFT, padx=(8, 0))

        # Project table
        columns = ("name", "rag", "status")
        self.project_table = ttk.Treeview(frame, columns=columns, show="headings", height=10)
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

        # AI analysis panel
        ai_frame = ttk.LabelFrame(frame, text="AI Analysis (Ollama)", padding=8)
        ai_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        llm_check = ttk.Checkbutton(
            ai_frame, text="Analyse projects with local LLM before generating",
            variable=self.use_llm_var, command=self._toggle_llm_options,
        )
        llm_check.grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(ai_frame, text="Model:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.model_entry = ttk.Entry(ai_frame, textvariable=self.model_var, width=20, state="disabled")
        self.model_entry.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        self.check_ollama_btn = ttk.Button(
            ai_frame, text="Check Ollama status",
            command=self._check_ollama, state="disabled",
        )
        self.check_ollama_btn.grid(row=1, column=2, sticky="w", padx=(10, 0), pady=(6, 0))

        self.ollama_status_var = tk.StringVar(value="")
        self.ollama_status_label = ttk.Label(
            ai_frame, textvariable=self.ollama_status_var,
            foreground="gray", wraplength=700, justify="left",
        )
        self.ollama_status_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        ai_frame.columnconfigure(1, weight=1)

        # Progress bar + status
        self.progress_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.progress_var, foreground="navy").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        self.progress_bar = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(4, 0))

        # Generate button
        self.generate_btn = ttk.Button(frame, text="Generate PowerPoint", command=self.generate_presentation)
        self.generate_btn.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(14, 0))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(5, weight=1)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _toggle_llm_options(self) -> None:
        state = "normal" if self.use_llm_var.get() else "disabled"
        self.model_entry.config(state=state)
        self.check_ollama_btn.config(state=state)
        if not self.use_llm_var.get():
            self.ollama_status_var.set("")

    def _check_ollama(self) -> None:
        self.ollama_status_var.set("Checking…")
        self.root.update_idletasks()
        available, msg = check_ollama_available(self.model_var.get().strip())
        color = "dark green" if available else "red"
        self.ollama_status_label.config(foreground=color)
        self.ollama_status_var.set(msg)

    def _set_progress(self, current: int, total: int, message: str) -> None:
        pct = int((current / total) * 100) if total else 0
        self.progress_bar["value"] = pct
        self.progress_var.set(message)
        self.root.update_idletasks()

    # ------------------------------------------------------------------
    # project table operations
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # generation
    # ------------------------------------------------------------------

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

        self.generate_btn.config(state="disabled")
        self.progress_bar["value"] = 0

        use_llm = self.use_llm_var.get()
        model = self.model_var.get().strip() or DEFAULT_MODEL
        report_title = self.title_var.get().strip() or "Project Status Report"
        report_date = self.date_var.get().strip() or datetime.now().strftime("%d %B %Y")
        projects_snapshot = list(self.projects)

        def run():
            try:
                data = build_data_from_simple_projects(
                    projects_snapshot,
                    report_title=report_title,
                    report_date=report_date,
                    use_llm=use_llm,
                    llm_model=model,
                    on_progress=self._set_progress,
                )
                build_deck(data, Path(output_path).resolve())
                self.root.after(0, lambda: self._on_generation_done(output_path, None))
            except Exception as exc:
                self.root.after(0, lambda: self._on_generation_done(output_path, exc))

        threading.Thread(target=run, daemon=True).start()

    def _on_generation_done(self, output_path: str, error: Exception | None) -> None:
        self.generate_btn.config(state="normal")
        self.progress_bar["value"] = 100
        if error:
            self.progress_var.set("Generation failed.")
            messagebox.showerror("Error", f"Failed to generate presentation:\n{error}")
        else:
            self.progress_var.set("Presentation created successfully.")
            messagebox.showinfo("Done", f"Presentation created:\n{output_path}")


def main() -> None:
    root = tk.Tk()
    StatusReportForm(root)
    root.mainloop()


if __name__ == "__main__":
    main()

