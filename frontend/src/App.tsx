import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type {
  CardEvent,
  CustomerProfile,
  CustomerSummary,
  MobileEvent,
  PartnerEvent,
  Stats,
  WebEvent,
} from "./types";

const CHANNEL_LABEL: Record<string, string> = {
  mobile_app: "Mobile App",
  partner_checkout: "Partner Checkout",
  web_portal: "Web Portal",
  cobranded_card: "Co-branded Card",
};

function fmtMoney(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function fmtNum(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("en-US").format(n);
}

function fmtDate(s: string | null | undefined): string {
  if (!s) return "—";
  return s.slice(0, 10);
}

function statusBadgeClass(status: string): string {
  const s = status.toLowerCase();
  if (s.includes("late") || s.includes("declined") || s.includes("failed") || s === "behind" || s === "frozen" || s === "closed") return "badge bad";
  if (s.includes("review") || s === "pays_minimum" || s === "revolves") return "badge warn";
  return "badge ok";
}

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [list, setList] = useState<CustomerSummary[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial data
  useEffect(() => {
    api.stats().then(setStats).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    setLoadingList(true);
    setError(null);
    const handle = setTimeout(async () => {
      try {
        const rows = query.trim()
          ? await api.search(query.trim())
          : await api.topCustomers();
        setList(rows);
        if (rows.length && !selected) setSelected(rows[0].email);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoadingList(false);
      }
    }, 200);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  useEffect(() => {
    if (!selected) {
      setProfile(null);
      return;
    }
    setLoadingProfile(true);
    setError(null);
    api
      .profile(selected)
      .then(setProfile)
      .catch((e) => setError(String(e)))
      .finally(() => setLoadingProfile(false));
  }, [selected]);

  const channels = useMemo(
    () => (profile?.channels_used ?? []).map((c) => CHANNEL_LABEL[c] || c),
    [profile]
  );

  return (
    <div className="app">
      <div className="header">
        <div className="brand">
          <div className="brand-mark">PL</div>
          <div>
            <div className="brand-name">PayLater Customer 360</div>
            <div className="brand-sub">
              Fintech BNPL · 4 sales channels · search by email or name
            </div>
          </div>
        </div>
        <a className="api-link" href="/docs" target="_blank" rel="noopener">
          REST API docs →
        </a>
      </div>

      {stats && (
        <div className="stats">
          <Stat label="Customers" value={fmtNum(stats.total_customers)} />
          <Stat label="Multi-channel" value={fmtNum(stats.multi_channel_customers)} />
          <Stat label="Mobile orders" value={fmtNum(stats.total_mobile_orders)} />
          <Stat label="Partner loans" value={fmtNum(stats.total_partner_loans)} />
          <Stat label="Web apps" value={fmtNum(stats.total_web_applications)} />
          <Stat label="Card accounts" value={fmtNum(stats.total_card_accounts)} />
          <Stat label="Mobile $" value={fmtMoney(stats.total_mobile_spend)} />
          <Stat label="Partner $" value={fmtMoney(stats.total_partner_principal)} />
          <Stat label="Web funded $" value={fmtMoney(stats.total_web_funded)} />
          <Stat label="Card balance $" value={fmtMoney(stats.total_card_balance)} />
        </div>
      )}

      <div className="search-bar">
        <input
          placeholder="Search by email or name (e.g. sofia, garcia, paylater-demo.com)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
      </div>

      {error && <div className="error">{error}</div>}

      <div className="layout">
        <div className="list">
          {loadingList && <div className="loading">Loading…</div>}
          {!loadingList && list.length === 0 && (
            <div className="loading">No matches.</div>
          )}
          {list.map((c) => (
            <div
              key={c.email}
              className={`list-item${selected === c.email ? " selected" : ""}`}
              onClick={() => setSelected(c.email)}
            >
              <div className="list-name">
                {c.first_name} {c.last_name}
              </div>
              <div className="list-email">{c.email}</div>
              <div className="chips">
                {c.channels_used.map((ch) => (
                  <span key={ch} className="chip active">
                    {CHANNEL_LABEL[ch] || ch}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="profile">
          {loadingProfile && <div className="loading">Loading profile…</div>}
          {!loadingProfile && !profile && (
            <div className="profile-empty">Select a customer to see their 360 view</div>
          )}
          {!loadingProfile && profile && (
            <>
              <div className="profile-header">
                <div>
                  <div className="profile-name">
                    {profile.first_name} {profile.last_name}
                  </div>
                  <div className="profile-email">{profile.email}</div>
                  <div className="profile-id">
                    {profile.customer_id} · last updated{" "}
                    {fmtDate(profile.profile_last_updated)}
                  </div>
                  <div className="profile-channels">
                    {channels.map((ch) => (
                      <span key={ch} className="chip active">
                        {ch}
                      </span>
                    ))}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div className="stat-label">Channels</div>
                  <div className="stat-value">{profile.channel_count}</div>
                </div>
              </div>

              <div className="stats">
                <Stat label="Mobile orders" value={fmtNum(profile.mobile_app_order_count)} />
                <Stat label="Mobile $" value={fmtMoney(profile.mobile_app_total_spend)} />
                <Stat label="Partner loans" value={fmtNum(profile.partner_loan_count)} />
                <Stat label="Partner $" value={fmtMoney(profile.partner_total_principal)} />
                <Stat label="Web apps" value={fmtNum(profile.web_application_count)} />
                <Stat label="Web funded $" value={fmtMoney(profile.web_total_funded)} />
                <Stat label="Cards" value={fmtNum(profile.card_account_count)} />
                <Stat label="Card balance" value={fmtMoney(profile.card_total_balance)} />
              </div>

              {profile.mobile_app_events.length > 0 && (
                <MobileSection events={profile.mobile_app_events} />
              )}
              {profile.partner_loan_events.length > 0 && (
                <PartnerSection events={profile.partner_loan_events} />
              )}
              {profile.web_application_events.length > 0 && (
                <WebSection events={profile.web_application_events} />
              )}
              {profile.card_account_events.length > 0 && (
                <CardSection events={profile.card_account_events} />
              )}

              <ApiHint email={profile.email} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function MobileSection({ events }: { events: MobileEvent[] }) {
  return (
    <div className="channel-section">
      <div className="channel-title">
        <h3>Mobile App purchases</h3>
        <div className="channel-summary">{events.length} events</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Order</th>
            <th>Category</th>
            <th>Plan</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.order_id}>
              <td>{e.order_id}</td>
              <td>{e.merchant_category}</td>
              <td>{e.bnpl_plan}</td>
              <td>{fmtMoney(e.order_amount)}</td>
              <td>
                <span className={statusBadgeClass(e.status)}>{e.status}</span>
              </td>
              <td>{fmtDate(e.order_ts)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PartnerSection({ events }: { events: PartnerEvent[] }) {
  return (
    <div className="channel-section">
      <div className="channel-title">
        <h3>Partner Checkout loans</h3>
        <div className="channel-summary">{events.length} events</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Loan</th>
            <th>Partner</th>
            <th>Principal</th>
            <th>APR</th>
            <th>Term</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.loan_id}>
              <td>{e.loan_id}</td>
              <td>{e.partner_name}</td>
              <td>{fmtMoney(e.principal_amount)}</td>
              <td>{e.apr_pct}%</td>
              <td>{e.term_months}mo</td>
              <td>
                <span className={statusBadgeClass(e.approval_status)}>
                  {e.approval_status}
                </span>
              </td>
              <td>{fmtDate(e.originated_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WebSection({ events }: { events: WebEvent[] }) {
  return (
    <div className="channel-section">
      <div className="channel-title">
        <h3>Web Portal applications</h3>
        <div className="channel-summary">{events.length} events</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>App ID</th>
            <th>UTM</th>
            <th>Purpose</th>
            <th>Requested</th>
            <th>Funded</th>
            <th>FICO</th>
            <th>KYC</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.application_id}>
              <td>{e.application_id}</td>
              <td>{e.utm_source}</td>
              <td>{e.loan_purpose}</td>
              <td>{fmtMoney(e.requested_amount)}</td>
              <td>{fmtMoney(e.funded_amount)}</td>
              <td>{e.credit_score}</td>
              <td>
                <span className={statusBadgeClass(e.kyc_status)}>{e.kyc_status}</span>
              </td>
              <td>{fmtDate(e.applied_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CardSection({ events }: { events: CardEvent[] }) {
  return (
    <div className="channel-section">
      <div className="channel-title">
        <h3>Co-branded Card accounts</h3>
        <div className="channel-summary">{events.length} events</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Account</th>
            <th>Card</th>
            <th>Limit</th>
            <th>Balance</th>
            <th>Util</th>
            <th>Tier</th>
            <th>Behavior</th>
            <th>Status</th>
            <th>Opened</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.account_id}>
              <td>{e.account_id}</td>
              <td>{e.card_partner}</td>
              <td>{fmtMoney(e.credit_limit)}</td>
              <td>{fmtMoney(e.current_balance)}</td>
              <td>{e.utilization_pct}%</td>
              <td>{e.rewards_tier}</td>
              <td>
                <span className={statusBadgeClass(e.payment_behavior)}>
                  {e.payment_behavior}
                </span>
              </td>
              <td>
                <span className={statusBadgeClass(e.account_status)}>
                  {e.account_status}
                </span>
              </td>
              <td>{fmtDate(e.account_opened)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ApiHint({ email }: { email: string }) {
  const url = `${window.location.origin}/api/customers/${encodeURIComponent(email)}`;
  return (
    <div className="channel-section">
      <div className="channel-title">
        <h3>Programmatic access</h3>
      </div>
      <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>
        Same data, via REST:
      </div>
      <div>
        <span className="kbd">GET</span> <a href={url} target="_blank" rel="noopener">{url}</a>
      </div>
    </div>
  );
}
