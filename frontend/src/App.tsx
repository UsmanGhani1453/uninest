import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from './api/client'
import type { Booking, Listing, User } from './api/client'
import './App.css'

type Page = 'browse' | 'detail' | 'auth' | 'owner' | 'student' | 'admin'
type Session = { token: string; user: User }
type ListingForm = {
  title: string
  description: string
  accommodation_type: Listing['accommodation_type']
  rent_per_month: string
  security_deposit: string
  address: string
  area: string
  university_names: string
  amenities: string
  image_urls: string
  bathrooms: string
  rooms: Array<{ id?: string; name: string; seat_count: string }>
}

const TODAY_DATE = new Date().toISOString().slice(0, 10)

const emptyListingForm: ListingForm = {
  title: '',
  description: '',
  accommodation_type: 'hostel',
  rent_per_month: '',
  security_deposit: '0',
  address: '',
  area: '',
  university_names: '',
  amenities: '',
  image_urls: '',
  bathrooms: '1',
  rooms: [{ name: 'Room 1', seat_count: '2' }],
}

function readSession(): Session | null {
  const value = localStorage.getItem('uninest.session')
  if (!value) return null
  try {
    return JSON.parse(value) as Session
  } catch {
    localStorage.removeItem('uninest.session')
    return null
  }
}

function money(value: number) {
  return new Intl.NumberFormat('en-PK', {
    style: 'currency',
    currency: 'PKR',
    maximumFractionDigits: 0,
  }).format(value)
}

function splitList(value: string) {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

function localDateString() {
  const today = new Date()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${today.getFullYear()}-${month}-${day}`
}

function listingToForm(listing: Listing): ListingForm {
  return {
    title: listing.title,
    description: listing.description,
    accommodation_type: listing.accommodation_type,
    rent_per_month: String(listing.rent_per_month),
    security_deposit: String(listing.security_deposit),
    address: listing.address,
    area: listing.area,
    university_names: listing.university_names.join(', '),
    amenities: listing.amenities.join(', '),
    image_urls: listing.image_urls.join(', '),
    bathrooms: String(listing.bathrooms),
    rooms: listing.rooms?.length
      ? listing.rooms.map((room) => ({ id: room.id, name: room.name, seat_count: String(room.seat_count) }))
      : [{ name: 'Room 1', seat_count: String(Math.max(listing.capacity, 1)) }],
  }
}

function App() {
  const [session, setSession] = useState<Session | null>(readSession)
  const [page, setPage] = useState<Page>('browse')
  const [listings, setListings] = useState<Listing[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null)
  const [pendingListings, setPendingListings] = useState<Listing[]>([])
  const [search, setSearch] = useState({ q: '', area: '', min_rent: '', max_rent: '', type: '' })
  const [appliedSearch, setAppliedSearch] = useState(search)
  const [listingForm, setListingForm] = useState<ListingForm>(emptyListingForm)
  const [editingListing, setEditingListing] = useState<Listing | null>(null)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [authRole, setAuthRole] = useState<'student' | 'owner'>('student')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [welcomeUser, setWelcomeUser] = useState<User | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const welcomeDialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = welcomeDialogRef.current
    if (!dialog) return
    if (welcomeUser && !dialog.open) dialog.showModal()
    else if (!welcomeUser && dialog.open) dialog.close()
  }, [welcomeUser])

  useEffect(() => {
    let active = true
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        if (page === 'browse') {
          const filters = new URLSearchParams()
          if (appliedSearch.q.trim()) filters.set('q', appliedSearch.q.trim())
          if (appliedSearch.area.trim()) filters.set('area', appliedSearch.area.trim())
          if (appliedSearch.min_rent) filters.set('min_rent', appliedSearch.min_rent)
          if (appliedSearch.max_rent) filters.set('max_rent', appliedSearch.max_rent)
          if (appliedSearch.type) filters.set('accommodation_type', appliedSearch.type)
          const result = await api.listings(filters)
          if (active) setListings(result)
        } else if (page === 'owner' && session?.user.role === 'owner') {
          const [ownListings, ownerBookings] = await Promise.all([
            api.myListings(session.token),
            api.ownerBookings(session.token),
          ])
          if (active) {
            setListings(ownListings)
            setBookings(ownerBookings)
          }
        } else if (page === 'student' && session?.user.role === 'student') {
          const result = await api.myBookings(session.token)
          if (active) setBookings(result)
        } else if (page === 'admin' && session?.user.role === 'admin') {
          const [result, adminBookings] = await Promise.all([
            api.pendingListings(session.token),
            api.ownerBookings(session.token),
          ])
          if (active) {
            setPendingListings(result)
            setBookings(adminBookings)
          }
        }
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Unable to load this page.')
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [page, session, refreshKey, appliedSearch])

  function goTo(nextPage: Page) {
    setError('')
    setNotice('')
    setSelectedListing(null)
    setPage(nextPage)
  }

  function signOut() {
    localStorage.removeItem('uninest.session')
    setSession(null)
    setWelcomeUser(null)
    setBookings([])
    goTo('browse')
  }

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setLoading(true)
    setError('')
    try {
      const result = authMode === 'login'
        ? await api.login(String(data.get('email')), String(data.get('password')))
        : await api.register({
          full_name: String(data.get('full_name')),
          email: String(data.get('email')),
          password: String(data.get('password')),
          role: authRole,
        })
      const nextSession = { token: result.access_token, user: result.user }
      localStorage.setItem('uninest.session', JSON.stringify(nextSession))
      setSession(nextSession)
      goTo(result.user.role === 'owner' ? 'owner' : result.user.role === 'admin' ? 'admin' : 'browse')
      setWelcomeUser(result.user)
      setRefreshKey((value) => value + 1)
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : 'Unable to authenticate.')
    } finally {
      setLoading(false)
    }
  }

  async function submitListing(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!session) return
    const payload = {
      title: listingForm.title,
      description: listingForm.description,
      accommodation_type: listingForm.accommodation_type,
      rent_per_month: Number(listingForm.rent_per_month),
      security_deposit: Number(listingForm.security_deposit || 0),
      address: listingForm.address,
      area: listingForm.area,
      city: 'Lahore',
      university_names: splitList(listingForm.university_names),
      amenities: splitList(listingForm.amenities),
      image_urls: splitList(listingForm.image_urls),
      bathrooms: Number(listingForm.bathrooms),
      rooms: listingForm.rooms.map((room) => ({
        ...(room.id ? { id: room.id } : {}),
        name: room.name,
        seat_count: Number(room.seat_count),
      })),
    }
    setLoading(true)
    setError('')
    try {
      if (editingListing) {
        await api.updateListing(session.token, editingListing.id, payload)
        setNotice('Listing updated and sent for admin review.')
      } else {
        await api.createListing(session.token, payload)
        setNotice('Listing submitted. It will be public after admin verification.')
      }
      setListingForm(emptyListingForm)
      setEditingListing(null)
      setRefreshKey((value) => value + 1)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save the listing.')
    } finally {
      setLoading(false)
    }
  }

  async function changeAvailability(listing: Listing) {
    if (!session) return
    setError('')
    try {
      await api.updateListing(session.token, listing.id, { is_available: !listing.is_available })
      setNotice(listing.is_available ? 'Listing marked unavailable.' : 'Listing marked available.')
      setRefreshKey((value) => value + 1)
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : 'Unable to update availability.')
    }
  }

  async function submitBooking(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!session || !selectedListing) return
    const data = new FormData(event.currentTarget)
    setLoading(true)
    setError('')
    try {
      await api.createBooking(session.token, {
        listing_id: selectedListing.id,
        move_in_date: String(data.get('move_in_date')),
        duration_months: Number(data.get('duration_months')),
        student_message: String(data.get('student_message') ?? ''),
      })
      goTo('student')
      setNotice('Booking request sent to the property owner.')
      setRefreshKey((value) => value + 1)
    } catch (bookingError) {
      setError(bookingError instanceof Error ? bookingError.message : 'Unable to send the booking request.')
    } finally {
      setLoading(false)
    }
  }

  async function updateBookingStatus(booking: Booking, status: 'approved' | 'rejected' | 'cancelled') {
    if (!session) return
    if (status === 'cancelled') {
      const prompt = booking.status === 'approved'
        ? 'Cancel this approved booking? Its seat will become available for these dates. No payment or refund will be processed.'
        : 'Cancel this booking request? No payment or refund will be processed.'
      if (!window.confirm(prompt)) return
    }
    setError('')
    try {
      const updated = await api.updateBooking(session.token, booking.id, status)
      setNotice(
        updated.status === 'rejected' && updated.resolution_note
          ? updated.resolution_note
          : updated.status === 'cancelled'
            ? 'Booking cancelled. Its seat is available again for these dates. No payment or refund was processed.'
            : `Booking request ${updated.status}.`,
      )
      setRefreshKey((value) => value + 1)
    } catch (bookingError) {
      setError(bookingError instanceof Error ? bookingError.message : 'Unable to update this booking.')
    }
  }

  async function reviewListing(listing: Listing, decision: 'verify' | 'reject') {
    if (!session) return
    setError('')
    try {
      if (decision === 'verify') {
        await api.verifyListing(session.token, listing.id)
      } else {
        const reason = window.prompt('Enter a reason for rejecting this listing:')
        if (reason === null) return
        if (reason.trim().length < 5) {
          setError('Please enter a rejection reason of at least 5 characters.')
          return
        }
        await api.rejectListing(session.token, listing.id, reason.trim())
      }
      setNotice(decision === 'verify' ? 'Listing verified and published.' : 'Listing rejected with feedback.')
      setRefreshKey((value) => value + 1)
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : 'Unable to review this listing.')
    }
  }

  function startEditing(listing: Listing) {
    setEditingListing(listing)
    setListingForm(listingToForm(listing))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function updateRoom(index: number, change: Partial<ListingForm['rooms'][number]>) {
    setListingForm((current) => ({
      ...current,
      rooms: current.rooms.map((room, roomIndex) => roomIndex === index ? { ...room, ...change } : room),
    }))
  }

  function addRoom() {
    setListingForm((current) => ({
      ...current,
      rooms: [...current.rooms, { name: `Room ${current.rooms.length + 1}`, seat_count: '2' }],
    }))
  }

  const nav = (
    <header className="topbar">
      <button className="brand" type="button" onClick={() => goTo('browse')}>
        <span className="brand-mark">U</span>
        <span>UniNest<span className="brand-dot">.</span></span>
      </button>
      <nav aria-label="Main navigation">
        <button className={page === 'browse' || page === 'detail' ? 'nav-link active' : 'nav-link'} onClick={() => goTo('browse')}>Find a place</button>
        {session?.user.role === 'student' && <button className={page === 'student' ? 'nav-link active' : 'nav-link'} onClick={() => goTo('student')}>My bookings</button>}
        {session?.user.role === 'owner' && <button className={page === 'owner' ? 'nav-link active' : 'nav-link'} onClick={() => goTo('owner')}>Owner dashboard</button>}
        {session?.user.role === 'admin' && <button className={page === 'admin' ? 'nav-link active' : 'nav-link'} onClick={() => goTo('admin')}>Review listings</button>}
      </nav>
      <div className="account-actions">
        {session
          ? <><span className="user-greeting">Hi, {session.user.full_name.split(' ')[0]}</span><button className="button button-outline button-small" onClick={signOut}>Sign out</button></>
          : <button className="button button-outline button-small" onClick={() => goTo('auth')}>Sign in</button>}
      </div>
    </header>
  )

  return (
    <div className="app-shell">
      {nav}
      <main>
        {error && <div className="alert alert-error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}
        {notice && <div className="alert alert-success" role="status">{notice}<button aria-label="Dismiss message" onClick={() => setNotice('')}>×</button></div>}
        {loading && <div className="loading-bar" aria-label="Loading" />}

        {page === 'browse' && (
          <>
            <section className="hero-section">
              <div className="hero-copy">
                <span className="eyebrow"><span className="eyebrow-dot" /> MADE FOR STUDENT LIFE IN LAHORE</span>
                <h1>Find a place<br />to <em>feel at home.</em></h1>
                <p>Discover verified hostels, apartments and rooms near the places that matter to you.</p>
              </div>
              <div className="hero-art" aria-hidden="true">
                <div className="art-sun" />
                <div className="art-building building-back"><span /><span /><span /><span /></div>
                <div className="art-building building-front"><span /><span /><span /><span /><span /><span /></div>
                <div className="art-plant"><i /><i /><i /><b /></div>
                <div className="art-caption">Your next chapter starts here</div>
              </div>
              <form className="search-panel" onSubmit={(event) => { event.preventDefault(); setAppliedSearch(search) }}>
                <label className="search-field">
                  <span>Area in Lahore</span>
                  <input value={search.area} onChange={(event) => setSearch({ ...search, area: event.target.value })} placeholder="e.g. Johar Town" />
                </label>
                <label className="search-field">
                  <span>Monthly budget per seat</span>
                  <div className="budget-inputs">
                    <input inputMode="numeric" value={search.min_rent} onChange={(event) => setSearch({ ...search, min_rent: event.target.value })} placeholder="Min" aria-label="Minimum monthly rent" />
                    <span>–</span>
                    <input inputMode="numeric" value={search.max_rent} onChange={(event) => setSearch({ ...search, max_rent: event.target.value })} placeholder="Max" aria-label="Maximum monthly rent" />
                  </div>
                </label>
                <label className="search-field type-field">
                  <span>Stay type</span>
                  <select value={search.type} onChange={(event) => setSearch({ ...search, type: event.target.value })}>
                    <option value="">Any type</option>
                    <option value="hostel">Hostel</option>
                    <option value="apartment">Apartment</option>
                    <option value="room">Room</option>
                  </select>
                </label>
                <button className="button button-primary search-button" type="submit">Search places <span>→</span></button>
              </form>
            </section>

            <section className="content-section listings-section">
              <div className="section-heading">
                <div><span className="eyebrow">A GOOD PLACE TO START</span><h2>Places students love</h2></div>
                <label className="keyword-search"><span aria-hidden="true">⌕</span><input value={search.q} onChange={(event) => setSearch({ ...search, q: event.target.value })} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); setAppliedSearch(search) } }} placeholder="Search listings" /></label>
              </div>
              {listings.length === 0 && !loading
                ? <div className="empty-state"><div className="empty-icon">⌂</div><h3>No places found yet</h3><p>Try another area or budget. Verified listings will appear here.</p></div>
                : <div className="listing-grid">{listings.map((listing, index) => (
                  <article className="listing-card" key={listing.id}>
                    <button className={`listing-image image-tone-${index % 4}`} onClick={() => { setSelectedListing(listing); setPage('detail') }} aria-label={`View ${listing.title}`}>
                      <ListingCover listing={listing} />
                      <span className="verified-chip"><span>✓</span> Verified</span>
                    </button>
                    <div className="listing-card-body">
                      <div className="listing-card-top"><span className="listing-type">{listing.accommodation_type}</span><span className="listing-capacity">{listing.rooms?.length ?? listing.bedrooms} rooms · {listing.capacity} seats</span></div>
                      <button className="listing-title" onClick={() => { setSelectedListing(listing); setPage('detail') }}>{listing.title}</button>
                      <p className="listing-location"><span>⌖</span> {listing.area}, {listing.city}</p>
                      <div className="listing-card-footer"><strong>{money(listing.rent_per_month)}<small> / seat / month</small></strong><button aria-label={`See ${listing.title}`} onClick={() => { setSelectedListing(listing); setPage('detail') }}>View <span>→</span></button></div>
                    </div>
                  </article>
                ))}</div>}
            </section>
            <section className="trust-strip"><span>✓ Listings reviewed by our team</span><span>⌖ Student-friendly areas</span><span>♡ No booking fee collected online</span></section>
          </>
        )}

        {page === 'detail' && selectedListing && (
          <section className="content-section detail-section">
            <button className="back-link" onClick={() => goTo('browse')}>← Back to places</button>
            <div className="detail-layout">
              <article className="detail-main">
                <div className="detail-image">
                  <ListingCover listing={selectedListing} detail />
                  <span className="verified-chip"><span>✓</span> Verified listing</span>
                </div>
                <div className="detail-title-row"><div><span className="listing-type">{selectedListing.accommodation_type}</span><h1>{selectedListing.title}</h1><p className="listing-location">⌖ {selectedListing.address}, {selectedListing.area}, {selectedListing.city}</p></div><strong className="detail-price">{money(selectedListing.rent_per_month)}<small>/seat/month</small></strong></div>
                <div className="detail-facts"><span>{selectedListing.rooms?.length ?? selectedListing.bedrooms} rooms</span><span>{selectedListing.bathrooms} bathrooms</span><span>{selectedListing.capacity} seats total</span></div>
                {selectedListing.rooms?.length > 0 && <><h2>Rooms and seats</h2><div className="amenities">{selectedListing.rooms.map((room) => <span key={room.id}>{room.name}: {room.seat_count} seats</span>)}</div></>}
                <h2>About this place</h2><p className="detail-description">{selectedListing.description}</p>
                {selectedListing.amenities.length > 0 && <><h2>What this place offers</h2><div className="amenities">{selectedListing.amenities.map((amenity) => <span key={amenity}>✓ {amenity}</span>)}</div></>}
                {selectedListing.university_names.length > 0 && <p className="nearby-schools"><strong>Near:</strong> {selectedListing.university_names.join(' · ')}</p>}
              </article>
              <aside className="booking-card">
                <span className="eyebrow">MAKE IT YOURS</span><h2>Request this place</h2>
                <p>Request a seat at the monthly price shown. The owner approves the request and UniNest assigns the first available seat across the rooms.</p>
                {session?.user.role === 'student'
                  ? <form className="stacked-form" onSubmit={submitBooking}>
                    <label>Move-in date<input name="move_in_date" type="date" min={TODAY_DATE} required /></label>
                    <label>Length of stay<select name="duration_months" defaultValue="6"><option value="1">1 month</option><option value="3">3 months</option><option value="6">6 months</option><option value="12">12 months</option><option value="24">24 months</option></select></label>
                    <label>Message to owner<textarea name="student_message" rows={3} maxLength={1000} placeholder="Introduce yourself or ask a question" /></label>
                    <button className="button button-primary button-wide" disabled={loading}>Send booking request</button>
                  </form>
                  : <div className="sign-in-prompt"><p>Sign in as a student to request a booking.</p><button className="button button-primary button-wide" onClick={() => { setAuthMode('login'); goTo('auth') }}>Sign in to continue</button></div>}
                <div className="booking-note">No payment is taken online. A request is not a confirmed tenancy.</div>
              </aside>
            </div>
          </section>
        )}

        {page === 'auth' && (
          <section className="auth-section">
            <div className="auth-illustration"><span className="eyebrow">WELCOME TO UNINEST</span><h1>A place to<br /><em>belong.</em></h1><p>Find a verified home near your campus and settle into student life.</p><div className="auth-illustration-mark">U</div></div>
            <div className="auth-card">
              <div className="auth-tabs"><button className={authMode === 'login' ? 'selected' : ''} onClick={() => setAuthMode('login')}>Sign in</button><button className={authMode === 'register' ? 'selected' : ''} onClick={() => setAuthMode('register')}>Create account</button></div>
              <h2>{authMode === 'login' ? 'Welcome back' : 'Join the UniNest community'}</h2>
              <p className="muted">{authMode === 'login' ? 'Enter your details to continue.' : 'Create an account to find or list a place.'}</p>
              <form className="stacked-form" onSubmit={submitAuth}>
                {authMode === 'register' && <><label>Your name<input name="full_name" autoComplete="name" minLength={2} maxLength={100} placeholder="e.g. Ayesha Khan" required /></label><label className="role-choice">I am joining as<select value={authRole} onChange={(event) => setAuthRole(event.target.value as 'student' | 'owner')}><option value="student">A student</option><option value="owner">A property owner</option></select></label></>}
                <label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" required /></label>
                <label>Password<input name="password" type="password" autoComplete={authMode === 'login' ? 'current-password' : 'new-password'} minLength={8} maxLength={128} placeholder="At least 8 characters" required /></label>
                <button className="button button-primary button-wide" disabled={loading}>{authMode === 'login' ? 'Sign in' : 'Create account'} <span>→</span></button>
              </form>
              <button className="back-link auth-back" onClick={() => goTo('browse')}>← Browse without signing in</button>
            </div>
          </section>
        )}

        {page === 'owner' && session?.user.role === 'owner' && (
          <section className="dashboard-section content-section">
            <div className="dashboard-header"><div><span className="eyebrow">OWNER SPACE</span><h1>Your listings & requests</h1><p>Manage your property details and respond to student requests.</p></div><span className="dashboard-avatar">{session.user.full_name.slice(0, 1).toUpperCase()}</span></div>
            <div className="dashboard-columns">
              <section className="panel listing-form-panel"><div className="panel-heading"><div><span className="eyebrow">{editingListing ? 'UPDATE PROPERTY' : 'ADD A PROPERTY'}</span><h2>{editingListing ? 'Edit your listing' : 'List a place'}</h2></div></div>
                <form className="stacked-form listing-form" onSubmit={submitListing}>
                  <label>Listing title<input value={listingForm.title} onChange={(event) => setListingForm({ ...listingForm, title: event.target.value })} minLength={5} maxLength={140} required placeholder="A welcoming room near campus" /></label>
                  <label>Description<textarea value={listingForm.description} onChange={(event) => setListingForm({ ...listingForm, description: event.target.value })} minLength={20} maxLength={5000} rows={4} required placeholder="Tell students what makes this place special" /></label>
                  <div className="form-row"><label>Property type<select value={listingForm.accommodation_type} onChange={(event) => setListingForm({ ...listingForm, accommodation_type: event.target.value as ListingForm['accommodation_type'] })}><option value="hostel">Hostel</option><option value="apartment">Apartment</option><option value="room">Room</option></select></label><label>Area<input value={listingForm.area} onChange={(event) => setListingForm({ ...listingForm, area: event.target.value })} minLength={2} maxLength={100} required placeholder="Johar Town" /></label></div>
                  <label>Street address<input value={listingForm.address} onChange={(event) => setListingForm({ ...listingForm, address: event.target.value })} minLength={5} maxLength={500} required placeholder="Street address, Lahore" /></label>
                  <div className="form-row">                  <label>Monthly rent per seat (PKR)<input type="number" min="1" step="1" value={listingForm.rent_per_month} onChange={(event) => setListingForm({ ...listingForm, rent_per_month: event.target.value })} required /></label><label>Security deposit per seat (PKR)<input type="number" min="0" step="1" value={listingForm.security_deposit} onChange={(event) => setListingForm({ ...listingForm, security_deposit: event.target.value })} /></label></div>
                  <div className="form-row"><label>Bathrooms in property<input type="number" min="1" value={listingForm.bathrooms} onChange={(event) => setListingForm({ ...listingForm, bathrooms: event.target.value })} required /></label></div>
                  <fieldset className="room-editor"><legend>Room inventory</legend><p className="muted">Add each room and the number of bookable seats it contains.</p>
                  {listingForm.rooms.map((room, index) => <div className="room-editor-row" key={room.id ?? `room-${index}`}><label>Room name<input value={room.name} maxLength={80} onChange={(event) => updateRoom(index, { name: event.target.value })} required /></label><label>Seats<input type="number" min="1" max="100" value={room.seat_count} onChange={(event) => updateRoom(index, { seat_count: event.target.value })} required /></label>{listingForm.rooms.length > 1 && <button className="text-button remove-room" type="button" onClick={() => setListingForm((current) => ({ ...current, rooms: current.rooms.filter((_, roomIndex) => roomIndex !== index) }))}>Remove</button>}</div>)}
                  <button className="button button-outline button-small add-room" type="button" onClick={addRoom}>+ Add another room</button>
                  </fieldset>
                  <label>Nearby universities <small>Separate multiple values with commas</small><input value={listingForm.university_names} onChange={(event) => setListingForm({ ...listingForm, university_names: event.target.value })} placeholder="UOL, GCU" /></label>
                  <label>Amenities <small>Separate multiple values with commas</small><input value={listingForm.amenities} onChange={(event) => setListingForm({ ...listingForm, amenities: event.target.value })} placeholder="WiFi, laundry, furnished" /></label>
                  <label>Image URLs <small>Separate multiple URLs with commas</small><input value={listingForm.image_urls} onChange={(event) => setListingForm({ ...listingForm, image_urls: event.target.value })} placeholder="https://..." /></label>
                  <div className="form-actions"><button className="button button-primary" disabled={loading}>{editingListing ? 'Save changes' : 'Submit for review'}</button>{editingListing && <button className="button button-outline" type="button" onClick={() => { setEditingListing(null); setListingForm(emptyListingForm) }}>Cancel edit</button>}</div>
                  <p className="form-footnote">New or edited listings need admin verification before they appear publicly.</p>
                </form>
              </section>
              <div className="dashboard-side">
                <section className="panel"><div className="panel-heading"><div><span className="eyebrow">YOUR PROPERTIES</span><h2>My listings <span className="count-badge">{listings.length}</span></h2></div></div>
                  {listings.length === 0 ? <p className="muted empty-inline">Your listings will show here after you submit them.</p> : <div className="manage-list">{listings.map((listing) => <article className="manage-item" key={listing.id}><div className="manage-item-main"><strong>{listing.title}</strong><span>{listing.area} · {money(listing.rent_per_month)}/seat/mo · {listing.capacity} seats</span><span className={`status-pill ${listing.is_verified ? 'status-approved' : listing.is_rejected ? 'status-rejected' : 'status-pending'}`}>{listing.is_verified ? 'Verified' : listing.is_rejected ? 'Changes requested' : 'Under review'}</span>{listing.verification_note && <small className="review-note">Admin note: {listing.verification_note}</small>}</div><div className="manage-actions"><button className="text-button" onClick={() => startEditing(listing)}>Edit</button><button className="text-button" onClick={() => void changeAvailability(listing)}>{listing.is_available ? 'Mark unavailable' : 'Mark available'}</button></div></article>)}</div>}
                </section>
                <section className="panel"><div className="panel-heading"><div><span className="eyebrow">STUDENT INTEREST</span><h2>Booking requests <span className="count-badge">{bookings.length}</span></h2></div></div>
                  {bookings.length === 0 ? <p className="muted empty-inline">Student booking requests will appear here.</p> : <div className="manage-list">{bookings.map((booking) => <BookingCard key={booking.id} booking={booking} onChange={(status) => void updateBookingStatus(booking, status)} ownerView />)}</div>}
                </section>
              </div>
            </div>
          </section>
        )}

        {page === 'student' && session?.user.role === 'student' && (
          <section className="content-section dashboard-section">
            <div className="dashboard-header"><div><span className="eyebrow">STUDENT SPACE</span><h1>Your booking requests</h1><p>Keep track of places you’ve reached out to.</p></div><button className="button button-primary" onClick={() => goTo('browse')}>Explore places <span>→</span></button></div>
            {bookings.length === 0 ? <div className="empty-state panel-empty"><div className="empty-icon">⌂</div><h3>Your next home is out there</h3><p>You haven’t requested a booking yet. Explore verified places around Lahore.</p><button className="button button-primary" onClick={() => goTo('browse')}>Find a place</button></div> : <div className="booking-list">{bookings.map((booking) => <BookingCard key={booking.id} booking={booking} onChange={(status) => void updateBookingStatus(booking, status)} />)}</div>}
          </section>
        )}

        {page === 'admin' && session?.user.role === 'admin' && (
          <section className="content-section dashboard-section">
            <div className="dashboard-header"><div><span className="eyebrow">UNINEST OPERATIONS</span><h1>Listing review</h1><p>Check listing details before they become visible to students.</p></div><span className="review-count">{pendingListings.length} awaiting review</span></div>
            {pendingListings.length === 0 ? <div className="empty-state panel-empty"><div className="empty-icon">✓</div><h3>You’re all caught up</h3><p>There are no listings waiting for review.</p></div> : <div className="admin-list">{pendingListings.map((listing) => <article className="panel admin-card" key={listing.id}><div className="admin-listing-copy"><span className="listing-type">{listing.accommodation_type} · {listing.area}</span><h2>{listing.title}</h2><p>{listing.address}, {listing.city}</p><p className="admin-description">{listing.description}</p><div className="admin-tags"><span>{money(listing.rent_per_month)} / seat / month</span><span>{listing.capacity} seats in {(listing.rooms ?? []).length || listing.bedrooms} rooms</span>{(listing.rooms ?? []).map((room) => <span key={room.id}>{room.name}: {room.seat_count} seats</span>)}{(listing.university_names ?? []).map((university) => <span key={university}>{university}</span>)}</div><small>Owner ID: {listing.owner_id}</small></div><div className="admin-review-actions"><button className="button button-primary" onClick={() => void reviewListing(listing, 'verify')}>✓ Verify listing</button><button className="button button-outline reject-button" onClick={() => void reviewListing(listing, 'reject')}>Request changes</button></div></article>)}</div>}
            <section className="panel admin-bookings-panel"><div className="panel-heading"><div><span className="eyebrow">BOOKING MANAGEMENT</span><h2>Bookings <span className="count-badge">{bookings.length}</span></h2></div></div>
              <p className="muted">Admins can cancel bookings at any time. Cancelling an approved booking releases its seat for the requested dates; no payment or refund is processed.</p>
              {bookings.length === 0 ? <p className="muted empty-inline">There are no bookings to manage.</p> : <div className="manage-list">{bookings.map((booking) => <BookingCard key={booking.id} booking={booking} onChange={(status) => void updateBookingStatus(booking, status)} ownerView />)}</div>}
            </section>
          </section>
        )}
      </main>
      <footer className="site-footer"><button className="brand footer-brand" onClick={() => goTo('browse')}><span className="brand-mark">U</span><span>UniNest<span className="brand-dot">.</span></span></button><span>Find your space. Find your people.</span><span>Made for Lahore students</span></footer>
      <dialog
        ref={welcomeDialogRef}
        className="welcome-dialog"
        aria-labelledby="welcome-title"
        onCancel={(event) => {
          event.preventDefault()
          welcomeDialogRef.current?.close()
        }}
        onClose={() => setWelcomeUser(null)}
      >
        {welcomeUser && <>
          <span className="eyebrow">WELCOME TO UNINEST</span>
          <h2 id="welcome-title">Welcome, {welcomeUser.full_name}!</h2>
          <p>{welcomeUser.role === 'student'
            ? 'Find your next place and keep track of your booking requests from your student space.'
            : welcomeUser.role === 'owner'
              ? 'Manage your properties and respond to student booking requests from your owner dashboard.'
              : 'Review listings and manage bookings from your admin workspace.'}</p>
          <button className="button button-primary button-wide" autoFocus onClick={() => welcomeDialogRef.current?.close()}>
            Continue
          </button>
        </>}
      </dialog>
    </div>
  )
}

function ListingCover({ listing, detail = false }: { listing: Listing; detail?: boolean }) {
  const [imageFailed, setImageFailed] = useState(false)
  const initial = listing.accommodation_type === 'hostel' ? 'H' : listing.accommodation_type === 'room' ? 'R' : 'A'

  if (listing.image_urls[0] && !imageFailed) {
    return <img src={listing.image_urls[0]} alt={listing.title} onError={() => setImageFailed(true)} />
  }
  if (detail) {
    return <div className="detail-placeholder"><span>{listing.accommodation_type}</span><strong>{listing.area}</strong></div>
  }
  return <span className="image-initial">{initial}</span>
}

function BookingCard({ booking, onChange, ownerView = false }: {
  booking: Booking
  onChange: (status: 'approved' | 'rejected' | 'cancelled') => void
  ownerView?: boolean
}) {
  return (
    <article className="booking-item">
      <div className="booking-item-header"><div><span className="eyebrow">REQUEST {booking.id.slice(-6).toUpperCase()}</span><h3>{money(booking.monthly_rent_snapshot)}<small> / month</small></h3></div><span className={`status-pill status-${booking.status}`}>{booking.status}</span></div>
      <div className="booking-meta"><span>Move-in {booking.move_in_date}</span><span>{booking.duration_months} month{booking.duration_months === 1 ? '' : 's'}</span><span>Deposit {money(booking.security_deposit_snapshot)}</span></div>
      {booking.status === 'approved' && booking.room_name && booking.seat_number && <p className="assigned-seat">Assigned: {booking.room_name}, seat {booking.seat_number}</p>}
      {booking.resolution_note && <p className="review-note">{booking.resolution_note}</p>}
      {booking.status === 'cancelled' && booking.cancelled_at && <p className="muted">Cancelled on {booking.cancelled_at.slice(0, 10)}</p>}
      {booking.student_message && <p className="booking-message">“{booking.student_message}”</p>}
      <p className="booking-estimate">Commission estimate: {money(booking.commission_amount_snapshot)} ({Math.round(booking.commission_rate_snapshot * 100)}% of one month’s seat rent). No online payment is collected.</p>
      {booking.status === 'pending' && <div className="booking-actions">
        {ownerView
          ? <><button className="button button-primary button-small" onClick={() => onChange('approved')}>Approve</button><button className="button button-outline button-small" onClick={() => onChange('rejected')}>Reject</button></>
          : <button className="text-button cancel-booking" onClick={() => onChange('cancelled')}>Cancel request</button>}
      </div>}
      {booking.status === 'approved' && (ownerView || booking.move_in_date > localDateString()) && <div className="booking-actions">
        <button className="text-button cancel-booking" onClick={() => onChange('cancelled')}>Cancel booking</button>
      </div>}
      {!ownerView && booking.status === 'approved' && booking.move_in_date <= localDateString() && <p className="muted">After move-in, contact the property owner or UniNest admin to cancel.</p>}
    </article>
  )
}

export default App
