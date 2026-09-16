<template>
  <div class="min-h-screen p-4 md:p-8 flex flex-col items-center">
    <div class="w-full max-w-3xl space-y-8">
      
      <!-- Encabezado -->
      <header class="text-center space-y-2 mt-8">
        <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight text-white">Biblia Semántica</h1>
        <p class="text-gray-400 text-lg">Busca versículos por su significado o idea, no solo por palabras clave exactas.</p>
      </header>

      <!-- Barra de Búsqueda -->
      <form @submit.prevent="search" class="relative group mt-8">
        <input 
          v-model="query" 
          type="text" 
          placeholder="Ej: Dios cumple sus promesas..." 
          class="w-full px-6 py-5 rounded-2xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-lg text-lg transition-all"
        />
        <button 
          type="submit" 
          class="absolute right-3 top-3 bottom-3 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading || query.length < 2"
        >
          Buscar
        </button>
      </form>

      <!-- Estado de Carga (Spinner minimalista) -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-16 space-y-4 text-gray-400">
        <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p class="animate-pulse">Consultando a la Inteligencia Artificial...</p>
      </div>

      <!-- Errores -->
      <div v-else-if="error" class="p-6 rounded-xl bg-red-900/40 border border-red-800 text-red-200 text-center text-lg">
        {{ error }}
      </div>

      <!-- Resultados (Cards) -->
      <div v-else-if="results.length > 0" class="space-y-4">
        <p class="text-sm text-gray-400 mb-4 ml-1">Se encontraron {{ results.length }} resultados.</p>
        
        <div 
          v-for="(result, index) in results" 
          :key="index"
          class="bg-gray-800 rounded-2xl p-6 border border-gray-700 shadow-md hover:border-gray-500 transition-colors"
        >
          <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-3 gap-2">
            <h3 class="text-xl font-bold text-blue-400">
              {{ result.book }} - {{ result.chapter }}:{{ result.verse }}
            </h3>
            
            <!-- Etiqueta de Score condicional (solo visible si VITE_DEV_MODE es true) -->
            <span v-if="devMode" class="self-start sm:self-auto text-xs px-3 py-1 bg-gray-900 text-gray-400 border border-gray-700 rounded-full font-mono">
              Score: {{ result.score.toFixed(4) }}
            </span>
          </div>
          
          <!-- Contexto Semántico -->
          <div v-if="result.heading || result.label" class="mb-3 flex flex-wrap gap-2">
            <span v-if="result.heading" class="text-xs font-semibold px-2 py-1 bg-indigo-900/50 text-indigo-300 rounded border border-indigo-800/50">
              Tema: {{ result.heading }}
            </span>
            <span v-if="result.label" class="text-xs font-semibold px-2 py-1 bg-teal-900/50 text-teal-300 rounded border border-teal-800/50">
              Contexto: {{ result.label }}
            </span>
          </div>

          <p class="text-gray-100 leading-relaxed text-lg">"{{ result.text }}"</p>
        </div>
      </div>

      <!-- Estado Vacío -->
      <div v-else-if="searched" class="text-center py-16 text-gray-500 text-lg">
        No se encontraron versículos relevantes para tu búsqueda. Prueba con otras palabras.
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const query = ref('')
const results = ref([])
const loading = ref(false)
const error = ref(null)
const searched = ref(false)

// Leer variables de entorno de Vite
// En Vue 3 + Vite se accede mediante import.meta.env
const devMode = import.meta.env.VITE_DEV_MODE === 'true'
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const search = async () => {
  if (query.value.length < 2) return
  
  loading.value = true
  error.value = null
  searched.value = true
  results.value = []

  try {
    const params = new URLSearchParams({
      q: query.value,
      limit: 5 // límite predeterminado
    })
    
    // Petición al backend FastAPI
    const response = await fetch(`${apiUrl}/search?${params.toString()}`, {
      headers: {
        'Accept': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`)
    }
    
    const data = await response.json()
    results.value = data.results
    
  } catch (err) {
    console.error("Error realizando la búsqueda vectorial:", err)
    error.value = "Ocurrió un error al contactar con el buscador. Asegúrate de que el backend de FastAPI esté encendido y sin errores."
  } finally {
    loading.value = false
  }
}
</script>
