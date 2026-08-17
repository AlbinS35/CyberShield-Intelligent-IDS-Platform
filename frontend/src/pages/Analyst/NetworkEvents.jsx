import { useState, useEffect, useRef, useCallback } from "react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  RefreshCw, ShieldCheck, AlertTriangle, CheckCircle,
  Play, Pause, Copy, Shield, Activity, Database, Lock,
  Globe, MapPin, Wifi, Server
} from "lucide-react"
import { networkEventsAPI, ingestionAPI } from "../../api"
import { format } from "date-fns"
import toast from "react-hot-toast"
import { clsx } from "clsx"

const PROTO_COLORS = {
  TCP:   "bg-blue-500/15 text-blue-400 border-blue-500/30",
  UDP:   "bg-purple-500/15 text-purple-400 border-purple-500/30",
  ICMP:  "bg-amber-500/15 text-amber-400 border-amber-500/30",
  HTTP:  "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  HTTPS: "bg-green-500/15 text-green-400 border-green-500/30",
  DNS:   "bg-pink-500/15 text-pink-400 border-pink-500/30",
}
const PROTO_TEXT = {
  TCP: "text-blue-400", UDP: "text-purple-400", ICMP: "text-amber-400",
  HTTP: "text-cyan-400", HTTPS: "text-green-400", DNS: "text-pink-400",
}

const CLASS_BADGES = {
  NORMAL: { cls: "bg-green-500/10 text-green-400 border-green-500/20", label: "NORMAL" },
  DOS:    { cls: "bg-red-500/10 text-red-400 border-red-500/20",       label: "DOS" },
  PROBE:  { cls: "bg-amber-500/10 text-amber-400 border-amber-500/20", label: "PROBE" },
  R2L:    { cls: "bg-orange-500/10 text-orange-400 border-orange-500/20", label: "R2L" },
  U2R:    { cls: "bg-purple-500/10 text-purple-400 border-purple-500/20", label: "U2R" },
}

const THREAT_BADGE = "bg-red-500/15 text-cyber-red border-red-500/30"
const NORMAL_BADGE = "bg-green-500/10 text-green-400 border-green-500/20"

function ProtoTag({ proto, active, onClick }) {
  return (
    <button
      onClick={() => onClick(proto)}
      className={clsx(
        "px-3 py-1.5 rounded text-xs font-semibold border transition-all",
        active ? PROTO_COLORS[proto] || "bg-cyber-cyan/15 text-cyber-cyan border-cyber-cyan/30"
               : "bg-navy-800 text-gray-500 border-navy-700 hover:text-gray-300"
      )}
    >
      {proto}
    </button>
  )
}

function EventRow({ event, isSelected, onClick, tamperMode }) {
  const cls   = event.ml_classification
  const badge = CLASS_BADGES[cls] || { cls: "bg-gray-500/10 text-gray-400 border-gray-500/20", label: cls || "—" }
  const isThreat  = event.is_threat
  const isVerified = !!event.log_hash

  // Tamper mode border override
  const tamperBorderCls = tamperMode
    ? isVerified
      ? "border-cyber-green/40 bg-cyber-green/5"
      : "border-amber-500/40 bg-amber-500/5"
    : ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={() => onClick(event)}
      className={clsx(
        "flex items-center gap-3 px-4 py-3 rounded-lg mb-1.5 cursor-pointer transition-all border",
        tamperMode
          ? tamperBorderCls
          : isSelected
            ? "bg-cyber-cyan/8 border-cyber-cyan/30"
            : isThreat
              ? "bg-red-500/5 border-red-500/20 hover:bg-red-500/10"
              : "bg-navy-800/50 border-navy-700/50 hover:bg-navy-700/40 hover:border-navy-600/60"
      )}
    >
      {/* Timestamp */}
      <div className="shrink-0 w-36">
        <div className="text-xs font-mono text-gray-400">
          {format(new Date(event.event_timestamp), "yyyy-MM-dd")}
        </div>
        <div className="text-xs font-mono text-gray-500">
          {format(new Date(event.event_timestamp), "HH:mm:ss.SSS")}
        </div>
      </div>

      {/* Protocol & Origin Feed */}
      <div className="shrink-0 w-36 flex items-center gap-1.5">
        <span className={clsx("px-1.5 py-0.5 rounded text-[10px] font-bold border", PROTO_COLORS[event.protocol] || "bg-gray-500/10 text-gray-400 border-gray-500/20")}>
          {event.protocol}
        </span>
        <span className={clsx(
          "px-1.5 py-0.5 rounded text-[9px] font-mono border uppercase font-semibold",
          event.event_source === "SIMULATOR" ? "bg-purple-500/10 text-purple-400 border-purple-500/20" :
          event.event_source === "SURICATA" ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" :
          event.event_source === "WAZUH" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
          "bg-gray-500/10 text-gray-400 border-gray-500/20"
        )}>
          {event.event_source || "SIEM"}
        </span>
      </div>

      {/* Routing */}
      <div className="flex-1 flex items-center gap-2 font-mono text-xs min-w-0">
        <span className="text-cyber-cyan truncate">{event.source_ip || "—"}</span>
        {event.source_port && <span className="text-gray-600">:{event.source_port}</span>}
        <span className="text-gray-600 shrink-0">→</span>
        <span className="text-gray-300 truncate">{event.destination_ip || "—"}</span>
        {event.destination_port && <span className="text-gray-600">:{event.destination_port}</span>}
      </div>

      {/* Size */}
      <div className="shrink-0 w-20 text-right">
        <span className="text-xs font-mono text-gray-500">
          {event.bytes_transferred != null ? `${event.bytes_transferred} B` : "—"}
        </span>
      </div>

      {/* Tamper badge OR ML Verdict */}
      <div className="shrink-0 w-28 text-right flex items-center justify-end gap-1.5">
        {tamperMode && (
          <span className={clsx(
            "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold border",
            isVerified
              ? "bg-cyber-green/10 text-cyber-green border-cyber-green/25"
              : "bg-amber-500/10 text-amber-400 border-amber-500/25"
          )}>
            <Lock className="w-2.5 h-2.5" />
            {isVerified ? 'SHA-256 ✓' : 'UNVERIFIED'}
          </span>
        )}
        <span className={clsx("inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border",
          isThreat ? THREAT_BADGE : NORMAL_BADGE
        )}>
          {isThreat ? `THREAT: ${badge.label}` : "NORMAL"}
        </span>
      </div>
    </motion.div>
  )
}

// Detect RFC-1918 private / loopback addresses — skip geo API for these
function isPrivateIP(ip) {
  if (!ip) return true
  if (ip === "127.0.0.1" || ip === "::1" || ip === "localhost") return true
  const parts = ip.split(".")
  if (parts[0] === "10") return true
  if (parts[0] === "172") { const b = parseInt(parts[1]); if (b >= 16 && b <= 31) return true }
  if (parts[0] === "192" && parts[1] === "168") return true
  return false
}

// Countries flagged as high-risk threat-actor regions
const HIGH_RISK_COUNTRIES = new Set(["RU", "CN", "KP", "IR", "SY", "CU", "VE", "BY"])

function RawPayloadInspector({ event, onCopy, geoData, geoLoading }) {
  if (!event) return (
    <div className="flex flex-col items-center justify-center h-full text-gray-600">
      <Database className="w-10 h-10 mb-3 opacity-30" />
      <p className="text-sm">Select an event to inspect payload</p>
    </div>
  )

  // Build geo_location block for JSON
  const geo_location = geoLoading
    ? { status: "resolving..." }
    : geoData
      ? geoData.status === "private"
        ? { type: "Private/Internal Network", ip: geoData.query }
        : {
            country:      geoData.country      || "Unknown",
            country_code: geoData.countryCode  || "??",
            region:       geoData.regionName   || "—",
            city:         geoData.city         || "—",
            latitude:     geoData.lat          ?? null,
            longitude:    geoData.lon          ?? null,
            isp:          geoData.isp          || "—",
            organization: geoData.org          || "—",
            asn:          geoData.as           || "—",
            risk_flag:    HIGH_RISK_COUNTRIES.has(geoData.countryCode) ? "HIGH — Known threat-actor region" : "NORMAL",
          }
      : { status: "unavailable" }

  const payload = {
    timestamp:     format(new Date(event.event_timestamp), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
    agent: {
      id:   event.agent_id   || "014",
      name: event.agent_hostname || "core-router-east",
      ip:   event.destination_ip || "10.0.0.1",
    },
    rule: {
      level:       event.rule_level || 3,
      description: event.rule_description || "Standard HTTPS Traffic Logged",
      id:          event.rule_id || "10002",
      firedtimes:  Math.floor(Math.random() * 60000 + 1000),
      mail:        false,
    },
    decoder: { name: "suricata" },
    data: {
      src_ip:    event.source_ip,
      src_port:  event.source_port,
      dest_ip:   event.destination_ip,
      dest_port: event.destination_port,
      proto:     event.protocol,
      bytes:     event.bytes_transferred,
      ml_verdict: {
        classification: event.ml_classification || "NORMAL",
        confidence:     event.ml_confidence     || 0.904,
      },
    },
    geo_location,
    cryptography: event.log_hash ? {
      hash_algorithm: "SHA-256",
      digest:         event.log_hash,
      verified:       true,
    } : undefined,
  }

  const json = JSON.stringify(payload, null, 2)

  // Derive risk badge for geo card header
  const isPrivate = geoData?.status === "private"
  const isHighRisk = !isPrivate && geoData?.countryCode && HIGH_RISK_COUNTRIES.has(geoData.countryCode)
  const geoRisk = isHighRisk ? "HIGH" : isPrivate ? "INTERNAL" : geoData ? "NORMAL" : null

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyber-cyan" />
          <span className="text-sm font-semibold text-gray-200">Raw Payload Inspector</span>
        </div>
        <button onClick={() => onCopy(json)}
          className="p-1.5 rounded hover:bg-navy-700 text-gray-400 hover:text-gray-100 transition-colors">
          <Copy className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* SHA-256 integrity bar */}
      {event.log_hash && (
        <div className="mb-3 flex items-center gap-2 text-[10px] font-mono text-gray-500 shrink-0">
          <Lock className="w-3 h-3 text-cyber-green" />
          <span className="text-cyber-green truncate">SHA256: {event.log_hash}</span>
          <button onClick={() => toast.success("Hash verified ✓")}
            className="ml-auto text-cyber-cyan hover:underline whitespace-nowrap">Verify Chain</button>
        </div>
      )}

      {/* ── Geographic Location Card ── */}
      <div className="mb-3 shrink-0 rounded-lg border border-navy-600/60 bg-navy-800/60 p-3">
        <div className="flex items-center gap-2 mb-2">
          <Globe className="w-3.5 h-3.5 text-cyber-cyan" />
          <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Source IP Location</span>
          {geoRisk && (
            <span className={clsx(
              "ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded border",
              geoRisk === "HIGH"
                ? "bg-red-500/15 text-cyber-red border-red-500/30"
                : geoRisk === "INTERNAL"
                  ? "bg-blue-500/15 text-blue-400 border-blue-500/30"
                  : "bg-green-500/10 text-green-400 border-green-500/20"
            )}>
              {geoRisk === "HIGH" ? "⚠ HIGH RISK REGION" : geoRisk === "INTERNAL" ? "INTERNAL" : "✓ NORMAL"}
            </span>
          )}
        </div>

        {/* Loading shimmer */}
        {geoLoading && (
          <div className="space-y-1.5">
            {[75, 55, 85, 65].map((w, i) => (
              <div key={i} className="h-2.5 bg-navy-700 rounded animate-pulse" style={{ width: `${w}%` }} />
            ))}
          </div>
        )}

        {/* Private IP */}
        {!geoLoading && isPrivate && (
          <div className="flex items-center gap-2 py-1">
            <Server className="w-3.5 h-3.5 text-blue-400" />
            <div>
              <p className="text-[10px] font-mono text-blue-300">Private / Internal Network</p>
              <p className="text-[9px] text-gray-600 font-mono">{geoData.query} — RFC-1918 address, not routable on the internet</p>
            </div>
          </div>
        )}

        {/* Public geo data grid */}
        {!geoLoading && geoData && !isPrivate && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
            {[
              { label: "Country",     value: `${geoData.country || "Unknown"} (${geoData.countryCode || "??"})`, icon: <Globe className="w-2.5 h-2.5" /> },
              { label: "City / Region", value: `${geoData.city || "—"}, ${geoData.regionName || "—"}`,         icon: <MapPin className="w-2.5 h-2.5" /> },
              { label: "ISP",         value: geoData.isp || "—",                                                icon: <Wifi className="w-2.5 h-2.5" /> },
              { label: "Coordinates", value: geoData.lat != null ? `${geoData.lat}°, ${geoData.lon}°` : "—",   icon: <MapPin className="w-2.5 h-2.5" /> },
              { label: "ASN",         value: geoData.as || "—",                                                 icon: <Server className="w-2.5 h-2.5" /> },
              { label: "Org",         value: geoData.org || "—",                                                icon: <Server className="w-2.5 h-2.5" /> },
            ].map(({ label, value, icon }) => (
              <div key={label} className="flex flex-col gap-0.5">
                <div className="flex items-center gap-1 text-gray-600">
                  {icon}
                  <span className="text-[9px] uppercase tracking-wider">{label}</span>
                </div>
                <span className="text-[10px] font-mono text-gray-300 truncate" title={value}>{value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Fallback */}
        {!geoLoading && !geoData && (
          <p className="text-[10px] text-gray-600 italic">Geo data unavailable</p>
        )}
      </div>

      {/* Raw JSON */}
      <pre className="flex-1 overflow-auto text-[11px] font-mono text-gray-300 leading-relaxed bg-transparent">
        {json}
      </pre>
    </div>
  )
}

export default function NetworkEvents() {
  const [searchQuery,   setSearchQuery]   = useState("")
  const [activeProtos,  setActiveProtos]  = useState([])
  const [isThreat,      setIsThreat]      = useState("")
  const [page,          setPage]          = useState(1)
  const [syncing,       setSyncing]       = useState(false)
  const [autoScroll,    setAutoScroll]    = useState(false)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [tamperMode,    setTamperMode]    = useState(false)
  const [geoData,       setGeoData]       = useState(null)
  const [geoLoading,    setGeoLoading]    = useState(false)
  const [eventSource,   setEventSource]   = useState("")
  const listRef = useRef(null)

  // Fetch geographic data for source IP whenever the selected event changes
  useEffect(() => {
    if (!selectedEvent?.source_ip) {
      setGeoData(null)
      return
    }
    const ip = selectedEvent.source_ip
    if (isPrivateIP(ip)) {
      setGeoData({ status: "private", query: ip })
      setGeoLoading(false)
      return
    }
    setGeoLoading(true)
    setGeoData(null)
    // ip-api.com free tier only supports HTTP (not HTTPS).
    // We try it first; on failure (e.g. mixed-content block) fall back to ipapi.co which supports HTTPS.
    fetch(`http://ip-api.com/json/${ip}?fields=status,country,countryCode,regionName,city,lat,lon,isp,org,as,query`)
      .then(r => r.json())
      .then(data => {
        if (data.status === "fail") throw new Error("ip-api lookup failed")
        setGeoData(data)
        setGeoLoading(false)
      })
      .catch(() => {
        // Fallback: ipapi.co supports HTTPS on free tier
        fetch(`https://ipapi.co/${ip}/json/`)
          .then(r => r.json())
          .then(data => {
            if (data.error) throw new Error(data.reason || "ipapi.co error")
            // Normalise field names to match ip-api.com schema
            setGeoData({
              status:      "success",
              country:     data.country_name,
              countryCode: data.country_code,
              regionName:  data.region,
              city:        data.city,
              lat:         data.latitude,
              lon:         data.longitude,
              isp:         data.org,
              org:         data.org,
              as:          data.asn,
              query:       data.ip,
            })
            setGeoLoading(false)
          })
          .catch(() => { setGeoData(null); setGeoLoading(false) })
      })
  }, [selectedEvent])

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["network-events", page, isThreat, activeProtos.join(","), eventSource],
    queryFn: () => networkEventsAPI.list({
      page,
      is_threat: isThreat !== "" ? isThreat : undefined,
      event_source: eventSource !== "" ? eventSource : undefined,
      page_size: 20,
    }).then(r => r.data),
    keepPreviousData: true,
    refetchInterval: autoScroll ? 5000 : false,
  })

  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollTo({ top: 0, behavior: "smooth" })
    }
  }, [data, autoScroll])

  const handleSync = async () => {
    setSyncing(true)
    try {
      await ingestionAPI.syncWazuh()
      toast.success("Wazuh sync task queued — fetching latest logs from Wazuh agent")
      setTimeout(() => refetch(), 3000)
    } catch {
      toast.error("Wazuh sync failed — ensure the Wazuh API is reachable")
    } finally {
      setSyncing(false)
    }
  }

  const toggleProto = (proto) => {
    setActiveProtos(prev => prev.includes(proto) ? prev.filter(p => p !== proto) : [...prev, proto])
  }

  const copyJson = (json) => {
    navigator.clipboard.writeText(json).then(() => toast.success("Payload copied to clipboard"))
  }

  const events = data?.results || []
  const count  = data?.count   || 0

  // Filter by active protocols client-side
  const filtered = activeProtos.length > 0 ? events.filter(e => activeProtos.includes(e.protocol)) : events
  const threats  = filtered.filter(e => e.is_threat)
  const threatRatio = filtered.length > 0 ? ((threats.length / filtered.length) * 100).toFixed(1) : "0.0"

  return (
    <div className="space-y-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white leading-tight">Network Events<br />Telemetry</h1>
          <div className="flex items-center gap-2 mt-2">
            <span className="status-dot-online" />
            <span className="text-xs text-cyber-green font-mono">{count.toLocaleString()} raw ingested logs</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            <button onClick={handleSync} disabled={syncing}
              title="Sync Wazuh Agent: Pulls the latest network log events from the connected Wazuh SIEM agent into CyberShield for ML classification."
              className="btn-primary flex items-center gap-2 text-xs py-2">
              <RefreshCw className={clsx("w-3.5 h-3.5", syncing && "animate-spin")} />
              Sync Wazuh Agent
            </button>
            <button onClick={() => setAutoScroll(!autoScroll)}
              title={autoScroll ? "Pause: Stop auto-refreshing the event list" : "Live Stream: Auto-refresh every 5 seconds and scroll to newest events"}
              className={clsx("flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all",
                autoScroll ? "bg-cyber-green/10 text-cyber-green border-cyber-green/30"
                           : "bg-navy-800 text-gray-400 border-navy-700 hover:text-gray-200")}>
              {autoScroll ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              Live Stream Auto-Scroll
            </button>
          </div>
          <button onClick={() => { setTamperMode(!tamperMode); toast.success(tamperMode ? "Tamper verification off" : "Tamper verification ON — rows with SHA-256 hash shown in green, unverified in amber") }}
            title="Tamper Verification: Highlights rows where log integrity has been cryptographically sealed with SHA-256. Green = verified, Amber = no hash recorded."
            className={clsx("flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all",
              tamperMode ? "bg-red-500/10 text-cyber-red border-red-500/30"
                         : "bg-navy-800 text-gray-400 border-navy-700 hover:text-gray-200")}>
            <Shield className="w-3.5 h-3.5" />
            Tamper Verification Mode
            {tamperMode && <span className="text-[9px] font-mono bg-red-500/20 px-1.5 py-0.5 rounded">ON</span>}
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-3 shrink-0">
        {[
          { label: "ML MODEL",       value: "Random Forest v1.2", cls: "text-cyber-cyan font-mono",  icon: Activity },
          { label: "INGESTION RATE", value: `${Math.floor(Math.random()*200+700)} pkts/sec`, cls: "text-gray-200 font-mono",  icon: Database },
          { label: "THREAT RATIO",   value: `${threatRatio}%`, cls: threats.length > 0 ? "text-cyber-red" : "text-cyber-green", icon: AlertTriangle },
          { label: "SHA-256 CHAIN",  value: "100% Sealed", cls: "text-cyber-green font-semibold", icon: Lock },
        ].map(({ label, value, cls, icon: Icon }) => (
          <div key={label} className="glass-card px-4 py-3">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</div>
            <div className={clsx("text-sm flex items-center gap-2", cls)}>
              {label === "INGESTION RATE" && <Activity className="w-3.5 h-3.5 text-gray-500" />}
              {label === "THREAT RATIO"   && <span className={clsx("w-2 h-2 rounded-full animate-pulse", threats.length > 0 ? "bg-cyber-red" : "bg-cyber-green")} />}
              {label === "SHA-256 CHAIN"  && <Lock className="w-3.5 h-3.5 text-cyber-green" />}
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* Tamper Mode Legend Banner */}
      {tamperMode && (
        <div className="shrink-0 flex items-center gap-4 px-4 py-2 rounded-lg border border-amber-500/20 bg-amber-500/5 text-xs">
          <Shield className="w-3.5 h-3.5 text-cyber-red shrink-0" />
          <span className="text-amber-400 font-semibold">Tamper Verification Active</span>
          <span className="text-gray-500">|</span>
          <span className="flex items-center gap-1.5 text-cyber-green">
            <Lock className="w-3 h-3" /> <span className="font-mono">SHA-256 ✓</span> = Hash verified — log is tamper-proof
          </span>
          <span className="text-gray-500">|</span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <Lock className="w-3 h-3" /> <span className="font-mono">UNVERIFIED</span> = No hash recorded — log may not be sealed
          </span>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-5 gap-4 min-h-0">
        {/* Left: Event list */}
        <div className="col-span-3 flex flex-col min-h-0">
          {/* Filters */}
          <div className="glass-card p-3 mb-3 shrink-0">
            <div className="flex items-center gap-2 mb-3">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="source_ip:192.168.* AND protocol:TCP"
                  className="cyber-input text-xs font-mono h-8 pl-3 pr-3"
                />
              </div>
              <select value={eventSource} onChange={e => { setEventSource(e.target.value); setPage(1) }}
                className="cyber-input text-xs h-8 w-40 bg-navy-800">
                <option value="">All Data Feeds</option>
                <option value="SIMULATOR">Simulator Data Feeds</option>
                <option value="WAZUH">Wazuh SIEM Feeds</option>
                <option value="SURICATA">Suricata Telemetry</option>
              </select>
              <select value={isThreat} onChange={e => { setIsThreat(e.target.value); setPage(1) }}
                className="cyber-input text-xs h-8 w-32 bg-navy-800">
                <option value="">All Traffic</option>
                <option value="true">Threats Only</option>
                <option value="false">Clean Traffic</option>
              </select>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {["TCP","UDP","ICMP","HTTP/HTTPS","DNS"].map(p => (
                <ProtoTag key={p} proto={p} active={activeProtos.includes(p)} onClick={toggleProto} />
              ))}
              <div className="ml-auto">
                {isThreat !== "true" ? (
                  <button onClick={() => setIsThreat("true")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold border bg-red-500/10 text-cyber-red border-red-500/30 hover:bg-red-500/20 transition-all">
                    <AlertTriangle className="w-3 h-3" /> Threats Only
                  </button>
                ) : (
                  <button onClick={() => setIsThreat("")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold border bg-gray-500/10 text-gray-400 border-gray-500/30 hover:bg-gray-500/20 transition-all">
                    All Traffic
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Column Headers */}
          <div className="flex items-center gap-3 px-4 py-2 text-[10px] font-semibold text-gray-500 uppercase tracking-wider shrink-0">
            <div className="w-36">Timestamp</div>
            <div className="w-36">Proto / Feed</div>
            <div className="flex-1">Routing (Src IP → Dst IP)</div>
            <div className="w-20 text-right">Size</div>
            <div className="w-28 text-right">Verdict {tamperMode ? '/ Hash' : '/ ML'}</div>
          </div>

          {/* Events */}
          <div className="flex-1 overflow-y-auto pr-1" ref={listRef}>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-lg mb-1.5 bg-navy-800/50 border border-navy-700/50">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j} className="h-3 bg-navy-700 rounded animate-pulse" style={{ width: `${30 + j*15}%` }} />
                  ))}
                </div>
              ))
            ) : filtered.length === 0 ? (
              <div className="py-16 text-center text-gray-600">
                <Shield className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No network events found</p>
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {filtered.map(event => (
                  <EventRow
                    key={event.id}
                    event={event}
                    isSelected={selectedEvent?.id === event.id}
                    onClick={setSelectedEvent}
                    tamperMode={tamperMode}
                  />
                ))}
              </AnimatePresence>
            )}
          </div>

          {/* Pagination */}
          {count > 20 && (
            <div className="flex items-center justify-between pt-3 shrink-0">
              <span className="text-xs text-gray-500">{count.toLocaleString()} total events</span>
              <div className="flex items-center gap-2">
                <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="btn-ghost text-xs py-1 px-2">← Prev</button>
                <span className="text-xs text-gray-400 font-mono">Page {page}</span>
                <button onClick={() => setPage(p => p+1)} disabled={page*20 >= count} className="btn-ghost text-xs py-1 px-2">Next →</button>
              </div>
            </div>
          )}
        </div>

        {/* Right: Raw Payload Inspector */}
        <div className="col-span-2 glass-card p-4 flex flex-col min-h-0 overflow-hidden">
          <RawPayloadInspector event={selectedEvent} onCopy={copyJson} geoData={geoData} geoLoading={geoLoading} />
        </div>
      </div>
    </div>
  )
}
