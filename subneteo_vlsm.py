import ipaddress
import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk


@dataclass(frozen=True)
class Solicitud:
    nombre: str
    hosts: int
    orden: int


@dataclass(frozen=True)
class Resultado:
    nombre: str
    hosts: int
    red: ipaddress.IPv4Network


def prefijo_para_hosts(hosts: int) -> int:
    """Calcula el prefijo mínimo reservando red y broadcast."""
    if hosts < 1:
        raise ValueError("Los hosts deben ser mayores que cero.")
    bits_host = max(2, math.ceil(math.log2(hosts + 2)))
    return 32 - bits_host


def calcular_vlsm(red_principal: str, solicitudes: list[Solicitud]) -> list[Resultado]:
    try:
        principal = ipaddress.ip_network(red_principal.strip(), strict=False)
    except ValueError as exc:
        raise ValueError("IP o prefijo inválido. Ejemplo: 172.19.0.0/16") from exc

    if principal.version != 4:
        raise ValueError("Solo se admiten direcciones IPv4.")
    if not solicitudes:
        raise ValueError("Agrega al menos una red o VLAN.")

    # VLSM asigna primero las necesidades de mayor tamaño.
    ordenadas = sorted(solicitudes, key=lambda s: (-s.hosts, s.orden))
    cursor = int(principal.network_address)
    limite = int(principal.broadcast_address)
    resultados = []

    for solicitud in ordenadas:
        prefijo = prefijo_para_hosts(solicitud.hosts)
        if prefijo < principal.prefixlen:
            raise ValueError(
                f"{solicitud.nombre} necesita /{prefijo}, pero la red principal es "
                f"/{principal.prefixlen}."
            )

        tamano = 1 << (32 - prefijo)
        inicio = ((cursor + tamano - 1) // tamano) * tamano
        subred = ipaddress.ip_network((inicio, prefijo))
        if int(subred.broadcast_address) > limite:
            raise ValueError(
                f"No hay espacio suficiente en {principal.with_prefixlen} para todas las redes."
            )

        resultados.append(Resultado(solicitud.nombre, solicitud.hosts, subred))
        cursor = int(subred.broadcast_address) + 1

    return resultados


class Calculadora(tk.Tk):
    FONDO = "#090b10"
    PANEL = "#141923"
    CAMPO = "#1c2431"
    TEXTO = "#f1f5f9"
    SUAVE = "#9ca3af"
    AZUL = "#38bdf8"
    BORDE = "#303b4d"

    def __init__(self) -> None:
        super().__init__()
        self.title("Calculadora de subnetting VLSM")
        self.geometry("1160x650")
        self.minsize(900, 540)
        self.configure(bg=self.FONDO)
        self.solicitudes: list[Solicitud] = []
        self._estilos()
        self._interfaz()

    def _estilos(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=self.FONDO, foreground=self.TEXTO, font=("Segoe UI", 10))
        s.configure("TFrame", background=self.FONDO)
        s.configure("TLabel", background=self.FONDO, foreground=self.TEXTO)
        s.configure("Titulo.TLabel", foreground=self.AZUL, font=("Segoe UI", 20, "bold"))
        s.configure("Suave.TLabel", foreground=self.SUAVE)
        s.configure("TLabelframe", background=self.PANEL, foreground=self.AZUL,
                    bordercolor=self.BORDE, relief="solid")
        s.configure("TLabelframe.Label", background=self.PANEL, foreground=self.AZUL,
                    font=("Segoe UI", 10, "bold"))
        s.configure("Panel.TLabel", background=self.PANEL, foreground=self.TEXTO)
        s.configure("TEntry", fieldbackground=self.CAMPO, foreground=self.TEXTO,
                    insertcolor=self.TEXTO, bordercolor=self.BORDE, padding=7)
        s.configure("TButton", background=self.CAMPO, foreground=self.TEXTO,
                    bordercolor=self.BORDE, padding=(10, 7))
        s.map("TButton", background=[("active", "#283548")])
        s.configure("Calcular.TButton", background="#0369a1", foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=(14, 8))
        s.map("Calcular.TButton", background=[("active", "#0284c7")])
        s.configure("Treeview", background=self.PANEL, fieldbackground=self.PANEL,
                    foreground=self.TEXTO, rowheight=30, bordercolor=self.BORDE)
        s.map("Treeview", background=[("selected", "#075985")],
              foreground=[("selected", "white")])
        s.configure("Treeview.Heading", background=self.CAMPO, foreground=self.AZUL,
                    font=("Segoe UI", 9, "bold"), relief="flat")

    def _interfaz(self) -> None:
        contenido = ttk.Frame(self, padding=20)
        contenido.pack(fill="both", expand=True)

        ttk.Label(contenido, text="Calculadora de subnetting VLSM",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(contenido, text="Ingresa la red principal y los hosts de cada red o VLAN.",
                  style="Suave.TLabel").pack(anchor="w", pady=(2, 15))

        entrada = ttk.LabelFrame(contenido, text="DATOS", padding=12)
        entrada.pack(fill="x")
        for columna, texto in enumerate(("Red principal", "Nombre de red o VLAN", "Hosts")):
            ttk.Label(entrada, text=texto, style="Panel.TLabel").grid(
                row=0, column=columna, sticky="w"
            )

        self.campo_principal = ttk.Entry(entrada, width=28, font=("Consolas", 11))
        self.campo_principal.insert(0, "172.19.0.0/16")
        self.campo_nombre = ttk.Entry(entrada, width=30)
        self.campo_hosts = ttk.Entry(entrada, width=15)
        self.campo_principal.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(4, 10))
        self.campo_nombre.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(4, 10))
        self.campo_hosts.grid(row=1, column=2, sticky="ew", padx=(0, 10), pady=(4, 10))
        self.campo_hosts.bind("<Return>", lambda _e: self._agregar())
        ttk.Button(entrada, text="Agregar", command=self._agregar).grid(
            row=1, column=3, sticky="ew", pady=(4, 10)
        )
        entrada.columnconfigure(0, weight=1)
        entrada.columnconfigure(1, weight=1)

        marco_lista = ttk.Frame(entrada)
        marco_lista.grid(row=2, column=0, columnspan=4, sticky="nsew")
        self.lista = tk.Listbox(
            marco_lista, height=5, bg=self.CAMPO, fg=self.TEXTO,
            selectbackground="#075985", selectforeground="white", relief="flat",
            highlightthickness=1, highlightbackground=self.BORDE, font=("Segoe UI", 10)
        )
        self.lista.pack(side="left", fill="both", expand=True)
        scroll_lista = ttk.Scrollbar(marco_lista, orient="vertical", command=self.lista.yview)
        scroll_lista.pack(side="right", fill="y")
        self.lista.configure(yscrollcommand=scroll_lista.set)

        botones = ttk.Frame(contenido)
        botones.pack(fill="x", pady=11)
        ttk.Button(botones, text="Eliminar", command=self._eliminar).pack(side="left")
        ttk.Button(botones, text="Limpiar", command=self._limpiar).pack(side="left", padx=7)
        ttk.Button(botones, text="Calcular", style="Calcular.TButton",
                   command=self._calcular).pack(side="right")

        resultado = ttk.LabelFrame(contenido, text="RESULTADOS", padding=8)
        resultado.pack(fill="both", expand=True)
        columnas = ("nombre", "hosts", "red", "primera", "ultima", "mascara", "broadcast")
        titulos = ("Red / VLAN", "Hosts", "IP / prefijo", "Primera IP",
                   "Última IP", "Máscara", "Broadcast")
        anchos = (150, 70, 150, 135, 135, 135, 135)
        self.tabla = ttk.Treeview(resultado, columns=columnas, show="headings")
        for columna, titulo, ancho in zip(columnas, titulos, anchos):
            self.tabla.heading(columna, text=titulo)
            self.tabla.column(columna, width=ancho, minwidth=65, anchor="center")
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(resultado, orient="vertical", command=self.tabla.yview)
        scroll.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=scroll.set)

        self.estado = ttk.Label(contenido, text="Las redes se asignan de mayor a menor.",
                                style="Suave.TLabel")
        self.estado.pack(anchor="w", pady=(9, 0))

    def _agregar(self) -> None:
        nombre = self.campo_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Dato faltante", "Escribe el nombre de la red o VLAN.")
            return
        try:
            hosts = int(self.campo_hosts.get())
            if hosts < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Dato incorrecto", "Hosts debe ser un entero mayor que cero.")
            return

        self.solicitudes.append(Solicitud(nombre, hosts, len(self.solicitudes)))
        self.lista.insert("end", f"{nombre}  —  {hosts} hosts")
        self.campo_nombre.delete(0, "end")
        self.campo_hosts.delete(0, "end")
        self.campo_nombre.focus_set()

    def _eliminar(self) -> None:
        seleccion = self.lista.curselection()
        if seleccion:
            indice = seleccion[0]
            self.lista.delete(indice)
            del self.solicitudes[indice]

    def _vaciar_tabla(self) -> None:
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

    def _limpiar(self) -> None:
        self.solicitudes.clear()
        self.lista.delete(0, "end")
        self._vaciar_tabla()
        self.estado.configure(text="Agrega las redes que necesitas calcular.")

    def _calcular(self) -> None:
        self._vaciar_tabla()
        try:
            resultados = calcular_vlsm(self.campo_principal.get(), self.solicitudes)
        except ValueError as exc:
            messagebox.showerror("No se pudo calcular", str(exc))
            return

        for resultado in resultados:
            red = resultado.red
            self.tabla.insert("", "end", values=(
                resultado.nombre,
                resultado.hosts,
                red.with_prefixlen,
                red.network_address + 1,
                red.broadcast_address - 1,
                red.netmask,
                red.broadcast_address,
            ))
        self.estado.configure(text=f"Cálculo completado: {len(resultados)} redes.")


if __name__ == "__main__":
    Calculadora().mainloop()
