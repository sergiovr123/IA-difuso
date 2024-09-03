import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from finta import TA
import yfinance as yf
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Variable global para mantener el canvas actual
current_canvas = None

# Función para obtener datos de BTC usando yfinance
def get_btc_data(start_date, end_date):
    try:
        # Descargar datos históricos de BTC usando las fechas proporcionadas
        df = yf.download('BTC-USD', start=start_date, end=end_date, interval='1d')
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron obtener los datos: {e}")
        return pd.DataFrame()

# Función para analizar los datos usando finta
def analyze_data(df):
    df['SMA30'] = TA.SMA(df, 30)
    df['RSI14'] = TA.RSI(df, 14)
    
    # Definición de variables difusas
    rsi = ctrl.Antecedent(np.arange(0, 101, 1), 'RSI')
    decision = ctrl.Consequent(np.arange(0, 11, 1), 'Decision')
    
    # Funciones de membresía para RSI
    rsi['low'] = fuzz.trimf(rsi.universe, [0, 0, 30])
    rsi['medium'] = fuzz.trimf(rsi.universe, [20, 50, 80])
    rsi['high'] = fuzz.trimf(rsi.universe, [70, 100, 100])
    
    # Funciones de membresía para la decisión
    decision['sell'] = fuzz.trimf(decision.universe, [0, 0, 5])
    decision['hold'] = fuzz.trimf(decision.universe, [0, 5, 10])
    decision['buy'] = fuzz.trimf(decision.universe, [5, 10, 10])
    
    # Reglas difusas
    rule1 = ctrl.Rule(rsi['low'], decision['buy'])
    rule2 = ctrl.Rule(rsi['high'], decision['sell'])
    rule3 = ctrl.Rule(rsi['medium'], decision['hold'])
    
    # Sistema de control difuso
    decision_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
    decision_sim = ctrl.ControlSystemSimulation(decision_ctrl)
    
    # Evaluar las reglas con el RSI actual
    rsi_value = df['RSI14'].iloc[-1]
    decision_sim.input['RSI'] = rsi_value
    decision_sim.compute()
    
    # Determinar la recomendación
    recommendation_value = decision_sim.output['Decision']
    if recommendation_value >= 7:
        recommendation = "Comprar"
    elif recommendation_value <= 3:
        recommendation = "Vender"
    else:
        recommendation = "Mantener"
    
    return recommendation

# Función para mostrar el gráfico
def plot_data(df):
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True)

    # Gráfico del precio
    ax1.plot(df['Date'], df['Close'], label='BTC Price', color='blue')
    ax1.plot(df['Date'], df['SMA30'], label='SMA 30', color='red')
    ax1.set_ylabel('Precio (USD)')
    ax1.set_title('Gráfico del BTC')
    ax1.legend()
    
    # Gráfico del RSI
    ax2.plot(df['Date'], df['RSI14'], label='RSI 14', color='green')
    ax2.axhline(y=70, color='r', linestyle='--', label='Sobrecompra')
    ax2.axhline(y=30, color='b', linestyle='--', label='Sobreventa')
    ax2.set_xlabel('Fecha')
    ax2.set_ylabel('RSI')
    ax2.set_title('RSI del BTC')
    ax2.legend()
    
    return fig

# Función para actualizar la interfaz gráfica
def update_gui():
    global current_canvas  # Declarar la variable global
    
    start_date = entry_start_date.get()
    end_date = entry_end_date.get()
    
    if not start_date or not end_date:
        messagebox.showerror("Error", "Por favor, ingrese las fechas de inicio y fin.")
        return
    
    df = get_btc_data(start_date, end_date)
    
    if df.empty:
        return
    
    recommendation = analyze_data(df)
    
    fig = plot_data(df)
    
    # Mostrar recomendación en un cuadro de diálogo
    messagebox.showinfo("Recomendación", f"Recomendación: {recommendation}")
    
    # Eliminar el canvas anterior si existe
    if current_canvas is not None:
        current_canvas.get_tk_widget().destroy()
    
    # Mostrar gráfico en tkinter
    current_canvas = FigureCanvasTkAgg(fig, master=window)
    current_canvas.draw()
    current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Configuración de la interfaz gráfica
window = tk.Tk()
window.title("Análisis de BTC")
window.geometry("800x600")

# Etiquetas y campos de texto para las fechas
tk.Label(window, text="Fecha de Inicio (YYYY-MM-DD):").pack(pady=5)
entry_start_date = tk.Entry(window)
entry_start_date.pack(pady=5)

tk.Label(window, text="Fecha de Fin (YYYY-MM-DD):").pack(pady=5)
entry_end_date = tk.Entry(window)
entry_end_date.pack(pady=5)

# Botón para actualizar el análisis
button = tk.Button(window, text="Actualizar Análisis", command=update_gui)
button.pack(pady=20)

window.mainloop()
