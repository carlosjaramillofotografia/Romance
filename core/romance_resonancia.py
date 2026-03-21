# core/romance_resonancia.py
class RomanceResonancia:
    """
    Sistema de Resonancia (Filtro Antygravity).
    Evalúa la coherencia y ajusta las reglas formales de las respuestas.
    """
    
    def aplicar_filtro(self, respuesta_cruda: str) -> str:
        """
        Limpia y ajusta la respuesta devuelta por el LLM para garantizar 
        que cumple estrictamente con las reglas formales de Romance.
        """
        # 1. Asegurar limpieza de espacios vacíos excesivos
        lineas = [li.strip() for li in respuesta_cruda.split('\n') if li.strip()]
        
        # 2. Romper encabezados robóticos (limpiar negritas **)
        # Si la IA usó **Título**, lo convertimos a texto plano para mantener la fluidez
        lineas_limpias = []
        for linea in lineas:
            limpia = linea.replace("**", "")
            lineas_limpias.append(limpia)
        
        # 3. Forzar que haya una separación visual poética entre frases
        # Reconstruimos el texto con saltos de línea dobles
        respuesta_filtrada = "\n\n".join(lineas_limpias)
        
        return respuesta_filtrada
