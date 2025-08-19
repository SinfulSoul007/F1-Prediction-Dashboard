const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export interface Circuit {
  circuit_key: string
  name: string
  locality: string
  country: string
  latitude: number
  longitude: number
  distance_km?: number
  laps?: number
}

export interface Race {
  id: number
  round: number
  grand_prix: string
  race_date: string | null
  session_start: string | null
  circuit: Circuit | null
}

export interface Result {
  driver_code: string
  team: string
  grid: number
  finish_pos: number
  status: string
  pit_stops: number
  total_time_ms?: number
  fastest_lap_ms?: number
  tyre_stints?: string
}

export interface RaceDetails {
  id: number
  year: number
  round: number
  grand_prix: string
  race_date: string | null
  session_start: string | null
  circuit: Circuit | null
  results: Result[]
}

export interface WeatherData {
  timestamp: string
  temp_c: number
  wind_kph: number
  precip_prob: number
  precip_mm: number
  cloud_pct: number
  humidity_pct: number
  pressure_hpa: number
  track_wet: boolean
}

export interface PredictionWeights {
  track_suitability: number
  clean_air_pace: number
  qualifying_importance: number
  team_form: number
  weather_impact: number
  chaos_mode: boolean
}

export interface DriverPrediction {
  driver: string
  team: string
  win_probability: number
  top3_probability: number
}

export interface PredictionResponse {
  race_id: number
  year: number
  round: number
  grand_prix: string
  weights: PredictionWeights
  predictions: DriverPrediction[]
  explanation: string
}

class F1Api {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Seasons API
  async getAvailableSeasons(): Promise<{ seasons: number[] }> {
    return this.request('/seasons/')
  }

  async getSeasonRaces(year: number): Promise<{ year: number; races: Race[] }> {
    return this.request(`/seasons/${year}/races`)
  }

  // Races API
  async getRaceDetails(year: number, round: number): Promise<RaceDetails> {
    return this.request(`/races/${year}/${round}`)
  }

  async getRaceLaps(year: number, round: number, session: string = 'R'): Promise<unknown> {
    return this.request(`/races/${year}/${round}/laps?session=${session}`)
  }

  // Weather API
  async getRaceWeather(year: number, round: number): Promise<{
    race_id: number
    year: number
    round: number
    grand_prix: string
    weather: WeatherData[]
  }> {
    return this.request(`/weather/${year}/${round}`)
  }

  // Results API
  async getSeasonResults(year: number): Promise<{
    year: number
    races: Array<{
      race_id: number
      round: number
      grand_prix: string
      race_date: string | null
      circuit: Partial<Circuit> | null
      results: Result[]
    }>
  }> {
    return this.request(`/results/${year}`)
  }

  async getRaceResults(year: number, round: number): Promise<{
    race_id: number
    year: number
    round: number
    grand_prix: string
    race_date: string | null
    circuit: Circuit | null
    results: Result[]
  }> {
    return this.request(`/results/${year}/${round}`)
  }

  // Predictions API
  async predictRace(
    year: number, 
    round: number, 
    weights: Partial<PredictionWeights> = {}
  ): Promise<PredictionResponse> {
    return this.request(`/predictions/${year}/${round}`, {
      method: 'POST',
      body: JSON.stringify({ weights }),
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request('/health')
  }
}

export const api = new F1Api()
export default api