<template>
  <div class="min-h-screen p-4 md:p-8 flex flex-col items-center">
    <div class="w-full max-w-3xl space-y-8">
      
      <!-- Encabezado -->
      <header class="text-center space-y-2 mt-8">
        <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight text-white">Biblia Semántica</h1>
        <p class="text-gray-400 text-lg">Búsqueda Híbrida: Conceptos y palabras clave exactas.</p>
      </header>

      <!-- Barra de Búsqueda y Selector de Límite -->
      <form @submit.prevent="search(1)" class="relative group mt-8 flex flex-col sm:flex-row gap-3">
        <div class="relative flex-grow">
          <input 
            v-model="query" 
            type="text" 
            placeholder="Ej: Nabucodonosor rey de Babilonia..." 
            class="w-full px-6 py-5 rounded-2xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-lg text-lg transition-all"
          />
          <button 
            type="submit" 
            class="absolute right-3 top-3 bottom-3 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed hidden sm:block"
            :disabled="loading || query.length < 2"
          >
            Buscar
          </button>
        </div>
        
        <div class="flex gap-2">
          <select 
            v-model="limit" 
            class="px-5 py-4 rounded-xl bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-lg text-lg appearance-none cursor-pointer"
          >
            <option :value="5">5 resultados</option>
            <option :value="10">10 resultados</option>
            <option :value="20">20 resultados</option>
            <option :value="50">50 resultados</option>
          </select>
          
          <button 
            type="submit" 
            class="px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed sm:hidden flex-grow"
            :disabled="loading || query.length < 2"
          >
            Buscar
          </button>
        </div>
      </form>

      <!-- Estado de Carga -->
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
        <p class="text-sm text-gray-400 mb-4 ml-1">Página {{ currentPage }} - Mostrando hasta {{ limit }} resultados.</p>
        
        <div 
          v-for="(result, index) in results" 
          :key="index"
          class="bg-gray-800 rounded-2xl p-6 border border-gray-700 shadow-md hover:border-gray-500 transition-colors"
        >
          <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-3 gap-2">
            <h3 class="text-xl font-bold text-blue-400">
              {{ result.book }} - {{ result.chapter }}:{{ result.verse }}
            </h3>
            
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
        
        <!-- Paginación -->
        <div class="flex justify-center items-center gap-4 pt-6 pb-12">
          <button 
            @click="prevPage" 
            :disabled="currentPage === 1 || loading"
            class="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white font-medium rounded-xl disabled:opacity-30 disabled:cursor-not-allowed border border-gray-700 transition-colors"
          >
            ← Anterior
          </button>
          <span class="text-gray-400 font-medium">Página {{ currentPage }}</span>
          <button 
            @click="nextPage" 
            :disabled="!hasNextPage || loading"
            class="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white font-medium rounded-xl disabled:opacity-30 disabled:cursor-not-allowed border border-gray-700 transition-colors"
          >
            Siguiente →
          </button>
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
const limit = ref(10)
const results = ref([])
const loading = ref(false)
const error = ref(null)
const searched = ref(false)

// Paginación
const currentPage = ref(1)
const hasNextPage = ref(false)

const devMode = import.meta.env.VITE_DEV_MODE === 'true'
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const search = async (page = 1) => {
  if (query.value.length < 2) return
  
  loading.value = true
  error.value = null
  searched.value = true
  
  // Limpiamos los resultados si es una búsqueda nueva (página 1)
  if (page === 1) {
    results.value = []
  }

  try {
    const offset = (page - 1) * limit.value
    
    const params = new URLSearchParams({
      q: query.value,
      limit: limit.value,
      offset: offset
    })
    
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
    currentPage.value = page
    
    // Si la API devolvió la misma cantidad de resultados que el límite,
    // asumimos que probablemente haya una página siguiente.
    hasNextPage.value = data.results.length === parseInt(limit.value)
    
    // Si la API soporta offset, hacer scroll al inicio de los resultados
    window.scrollTo({ top: 0, behavior: 'smooth' })
    
  } catch (err) {
    console.error("Error realizando la búsqueda vectorial:", err)
    error.value = "Ocurrió un error al contactar con el buscador. Asegúrate de que el backend esté encendido."
  } finally {
    loading.value = false
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    search(currentPage.value - 1)
  }
}

const nextPage = () => {
  if (hasNextPage.value) {
    search(currentPage.value + 1)
  }
}
</script>
