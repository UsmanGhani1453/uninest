const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')

export type User = {
  id: string
  full_name: string
  email: string
  role: 'student' | 'owner' | 'admin'
  phone: string | null
  is_verified: boolean
}

export type ListingRoom = {
  id: string
  name: string
  seat_count: number
}

export type Listing = {
  id: string
  title: string
  description: string
  accommodation_type: 'hostel' | 'apartment' | 'room'
  rent_per_month: number
  security_deposit: number
  address: string
  area: string
  city: string
  university_names: string[]
  amenities: string[]
  image_urls: string[]
  bedrooms: number
  bathrooms: number
  capacity: number
  rooms: ListingRoom[]
  owner_id: string
  is_verified: boolean
  is_available: boolean
  is_rejected: boolean
  verification_note: string | null
  reviewed_at: string | null
  created_at?: string
}

export type Booking = {
  id: string
  listing_id: string
  student_id: string
  owner_id: string
  move_in_date: string
  duration_months: number
  room_id: string | null
  room_name: string | null
  seat_number: number | null
  monthly_rent_snapshot: number
  security_deposit_snapshot: number
  commission_rate_snapshot: number
  commission_amount_snapshot: number
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  resolution_note: string | null
  cancelled_at: string | null
  cancelled_by: string | null
  student_message: string | null
  created_at: string
}

type RequestOptions = {
  method?: string
  token?: string | null
  body?: unknown
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers()
  if (options.body !== undefined) headers.set('Content-Type', 'application/json')
  if (options.token) headers.set('Authorization', `Bearer ${options.token}`)

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })
  if (!response.ok) {
    const errorBody = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(errorBody?.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  register: (data: { full_name: string; email: string; password: string; role: 'student' | 'owner' }) =>
    request<{ access_token: string; user: User }>('/auth/register', { method: 'POST', body: data }),
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>('/auth/login', { method: 'POST', body: { email, password } }),
  listings: (filters: URLSearchParams = new URLSearchParams()) =>
    request<Listing[]>(`/listings${filters.size ? `?${filters.toString()}` : ''}`),
  listing: (id: string) => request<Listing>(`/listings/${encodeURIComponent(id)}`),
  myListings: (token: string) => request<Listing[]>('/listings/mine', { token }),
  createListing: (token: string, data: Record<string, unknown>) =>
    request<Listing>('/listings', { method: 'POST', token, body: data }),
  updateListing: (token: string, id: string, data: Record<string, unknown>) =>
    request<Listing>(`/listings/${encodeURIComponent(id)}`, { method: 'PATCH', token, body: data }),
  pendingListings: (token: string) => request<Listing[]>('/admin/listings/pending', { token }),
  verifyListing: (token: string, id: string) =>
    request(`/admin/listings/${encodeURIComponent(id)}/verify`, { method: 'PATCH', token }),
  rejectListing: (token: string, id: string, reason: string) =>
    request(`/admin/listings/${encodeURIComponent(id)}/reject`, { method: 'PATCH', token, body: { reason } }),
  createBooking: (token: string, data: { listing_id: string; move_in_date: string; duration_months: number; student_message: string }) =>
    request<Booking>('/bookings', { method: 'POST', token, body: data }),
  myBookings: (token: string) => request<Booking[]>('/bookings/mine', { token }),
  ownerBookings: (token: string) => request<Booking[]>('/bookings/owner', { token }),
  updateBooking: (token: string, id: string, status: 'approved' | 'rejected' | 'cancelled') =>
    request<Booking>(`/bookings/${encodeURIComponent(id)}/status`, { method: 'PATCH', token, body: { status } }),
}
