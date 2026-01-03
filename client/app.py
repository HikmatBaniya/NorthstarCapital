from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from dotenv import load_dotenv

from .llm_agent import LLMClient
from .mcp_client import MCPClient


class FinancialApp:
    def __init__(self, root: tk.Tk) -> None:
        load_dotenv()
        self.root = root
        self.root.title("Financial LLM")
        self.root.geometry("1020x700")
        self.root.configure(bg="#0a0f1e")

        self.history = []
        self.llm_client = None
        self.mcp_client = MCPClient()

        self._build_ui()

    def _build_ui(self) -> None:
        self._style = ttk.Style()
        self._style.theme_use("clam")
        self._style.configure("Neo.TFrame", background="#0a0f1e")
        self._style.configure("Neo.TLabel", background="#0a0f1e", foreground="#cbd5f5")
        self._style.configure(
            "Neo.TCheckbutton",
            background="#0a0f1e",
            foreground="#cbd5f5",
        )
        self._style.map(
            "Neo.TCheckbutton",
            foreground=[("active", "#f5f7ff")],
        )
        self._style.configure(
            "Neo.TButton",
            background="#1c2b4a",
            foreground="#e8f0ff",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 8),
        )
        self._style.map(
            "Neo.TButton",
            background=[("active", "#2a4172"), ("disabled", "#141b2c")],
            foreground=[("disabled", "#6f7a99")],
        )

        header = ttk.Frame(self.root, style="Neo.TFrame")
        header.pack(fill=tk.X, padx=12, pady=(10, 6))
        title = ttk.Label(
            header,
            text="FINANCIAL LLM",
            style="Neo.TLabel",
            font=("Segoe UI Semibold", 16),
        )
        title.pack(side=tk.LEFT)
        subtitle = ttk.Label(
            header,
            text="Realtime market intelligence",
            style="Neo.TLabel",
            font=("Segoe UI", 10),
        )
        subtitle.pack(side=tk.LEFT, padx=12)

        self.chat = ScrolledText(
            self.root,
            wrap=tk.WORD,
            height=28,
            state=tk.DISABLED,
            bg="#0f162a",
            fg="#e4ecff",
            insertbackground="#e4ecff",
            font=("Consolas", 11),
            relief=tk.FLAT,
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        options_frame = ttk.Frame(self.root, style="Neo.TFrame")
        options_frame.pack(fill=tk.X, padx=12, pady=(0, 4))

        self.use_memory_var = tk.BooleanVar(value=True)
        self.store_memory_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Use memory context",
            variable=self.use_memory_var,
            style="Neo.TCheckbutton",
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            options_frame,
            text="Store to memory",
            variable=self.store_memory_var,
            style="Neo.TCheckbutton",
        ).pack(side=tk.LEFT, padx=12)

        input_frame = ttk.Frame(self.root, style="Neo.TFrame")
        input_frame.pack(fill=tk.X, padx=12, pady=10)

        self.entry = tk.Entry(
            input_frame,
            bg="#10182b",
            fg="#e4ecff",
            insertbackground="#e4ecff",
            relief=tk.FLAT,
            font=("Consolas", 11),
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", lambda event: self.on_send())

        self.send_button = ttk.Button(
            input_frame, text="Transmit", command=self.on_send, style="Neo.TButton"
        )
        self.send_button.pack(side=tk.LEFT, padx=12)

        self.status = ttk.Label(
            self.root, text="Ready", style="Neo.TLabel", font=("Segoe UI", 9)
        )
        self.status.pack(fill=tk.X, padx=12, pady=(0, 10))

    def on_send(self) -> None:
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, tk.END)
        self._append_chat("User", user_text)
        self.send_button.config(state=tk.DISABLED)
        self.status.config(text="Thinking...")
        thread = threading.Thread(target=self._run_llm, args=(user_text,), daemon=True)
        thread.start()

    def _run_llm(self, user_text: str) -> None:
        try:
            if self.llm_client is None:
                self.llm_client = LLMClient()
            memory_context = ""
            if self.use_memory_var.get():
                memory_context = self._search_memory(user_text)
            response = self.llm_client.ask(
                user_text, self.llm_client.to_messages(self.history), memory_context
            )
            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": response})
            if self.store_memory_var.get():
                self._store_memory(user_text, response)
            self.root.after(0, lambda: self._append_chat("Assistant", response))
        except Exception as exc:
            err = str(exc)
            self.root.after(0, lambda e=err: self._append_chat("Error", e))
        finally:
            self.root.after(0, self._ready_state)

    def _store_memory(self, user_text: str, response: str) -> None:
        try:
            self.mcp_client.invoke(
                "memory.put", {"content": user_text, "tags": ["user"]}
            )
            self.mcp_client.invoke(
                "memory.put", {"content": response, "tags": ["assistant"]}
            )
        except Exception as exc:
            self.root.after(0, lambda: self._append_chat("Memory", str(exc)))

    def _search_memory(self, query: str) -> str:
        try:
            result = self.mcp_client.invoke("memory.search", {"query": query, "limit": 5})
            items = result.get("result", [])
            if not items:
                return ""
            parts = []
            for item in items:
                content = item.get("content", "")
                if content:
                    parts.append(content)
            return "\n".join(parts)
        except Exception:
            return ""

    def _append_chat(self, role: str, message: str) -> None:
        self.chat.config(state=tk.NORMAL)
        if role == "User":
            self.chat.insert(tk.END, f"[USER] {message}\n\n")
        elif role == "Assistant":
            self.chat.insert(tk.END, f"[AI] {message}\n\n")
        else:
            self.chat.insert(tk.END, f"[{role.upper()}] {message}\n\n")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _ready_state(self) -> None:
        self.send_button.config(state=tk.NORMAL)
        self.status.config(text="Ready")


def main() -> None:
    root = tk.Tk()
    app = FinancialApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
