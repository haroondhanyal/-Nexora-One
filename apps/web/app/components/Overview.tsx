import Image from "next/image";
import {
  Activity,
  ArrowRight,
  Boxes,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  ChevronRight,
  Circle,
  ClipboardCheck,
  Plus,
  ShieldCheck,
  Users,
} from "lucide-react";
import type { Store } from "../types";

type OverviewProps = {
  data: Store;
  go: (key: string) => void;
  workspaceName: string;
  localDemo: boolean;
};

export function Overview({ data, go, workspaceName, localDemo }: OverviewProps) {
  const branches = data.branches || [];
  const members = data.users || [];
  const leads = data.leads || [];
  const approvals = data.approvals || [];
  const activity = data.audit || [];
  const pendingApprovals = approvals.filter((row) =>
    !["approved", "rejected", "cancelled", "complete", "completed"].includes(
      String(row.Status || "").toLowerCase(),
    ),
  );

  const metrics = [
    { label: "Branches", value: branches.length, note: "Business locations", icon: Building2, key: "branches", tone: "blue" },
    { label: "Team members", value: members.length, note: "Workspace access", icon: Users, key: "users", tone: "green" },
    { label: "CRM leads", value: leads.length, note: "Customer opportunities", icon: BriefcaseBusiness, key: "leads", tone: "amber" },
    { label: "Needs attention", value: pendingApprovals.length, note: "Pending approvals", icon: ClipboardCheck, key: "approvals", tone: "violet" },
  ];

  const setupItems = [
    { label: "Workspace created", detail: workspaceName, done: true, key: "settings" },
    { label: "Add your first branch", detail: "Organize your teams by location", done: branches.length > 0, key: "branches" },
    { label: "Set up your team", detail: "Add employees and workspace access", done: members.length > 1, key: "employees" },
    { label: "Create a CRM lead", detail: "Keep track of a customer opportunity", done: leads.length > 0, key: "leads" },
  ];
  const completedSteps = setupItems.filter((item) => item.done).length;

  return (
    <div className="nexora-overview">
      <section className="overview-welcome">
        <div className="overview-welcome-copy">
          <div className="overview-brand-line">
            <Image src="/brand/nexora-one-mark.svg" width={88} height={92} alt="" />
            <span>NEXORA ONE</span>
            {localDemo && <span className="overview-env-tag">LOCAL PREVIEW</span>}
          </div>
          <p className="overview-overline">YOUR BUSINESS, IN ONE PLACE</p>
          <h2>Welcome to<br /><em>{workspaceName}</em></h2>
          <p className="overview-welcome-text">
            Your workspace is ready. Bring your people and daily operations together, one step at a time.
          </p>
          <div className="overview-welcome-actions">
            <button className="overview-primary-action" onClick={() => go("branches")}>
              <Plus size={16} /> Set up a branch
            </button>
            <button className="overview-secondary-action" onClick={() => go("employees")}>
              Explore people <ArrowRight size={15} />
            </button>
          </div>
        </div>
        <div className="overview-visual" aria-hidden="true">
          <div className="overview-visual-orbit orbit-a" />
          <div className="overview-visual-orbit orbit-b" />
          <div className="overview-visual-mark"><Image src="/brand/nexora-one-mark.svg" width={88} height={92} alt="" /></div>
          <span className="overview-float-card float-team"><Users size={15} /><span>People</span></span>
          <span className="overview-float-card float-ops"><Activity size={15} /><span>Operations</span></span>
          <span className="overview-float-card float-erp"><Boxes size={15} /><span>Business</span></span>
        </div>
        {localDemo && (
          <div className="overview-service-note">
            <ShieldCheck size={15} /> Local API connected <i /> Odoo is offline
          </div>
        )}
      </section>

      <section className="overview-metrics" aria-label="Workspace summary">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <button className="overview-metric" key={metric.key} onClick={() => go(metric.key)}>
              <span className={`overview-metric-icon ${metric.tone}`}><Icon size={18} /></span>
              <span className="overview-metric-copy"><small>{metric.label}</small><b>{metric.value}</b><span>{metric.note}</span></span>
              <ChevronRight className="overview-metric-arrow" size={16} />
            </button>
          );
        })}
      </section>

      <div className="overview-lower-grid">
        <section className="overview-panel overview-activity">
          <div className="overview-section-heading">
            <div><span className="overview-section-kicker">WORKSPACE LOG</span><h3>Recent activity</h3><p>Changes made across your Nexora One workspace.</p></div>
            <button className="overview-link" onClick={() => go("audit")}>Open audit log <ArrowRight size={14} /></button>
          </div>
          {activity.length ? (
            <div className="overview-activity-list">
              {activity.slice(0, 5).map((row) => (
                <div className="overview-activity-row" key={row.id}>
                  <span className="overview-activity-icon"><Activity size={15} /></span>
                  <span className="overview-activity-copy"><b>{row.Action}</b><small>{row.Record} · {row.Actor}</small></span>
                  <time>{row.Date}</time>
                </div>
              ))}
            </div>
          ) : (
            <div className="overview-empty-activity">
              <span><Activity size={19} /></span>
              <div><b>Your activity will show up here</b><p>When you add a branch, employee, or lead, you’ll see the latest changes in this space.</p></div>
            </div>
          )}
        </section>

        <section className="overview-panel overview-getting-started">
          <div className="overview-section-heading">
            <div><span className="overview-section-kicker">GETTING STARTED</span><h3>Build your workspace</h3><p>A few first steps to make it yours.</p></div>
            <span className="overview-progress-count">{completedSteps}/{setupItems.length}</span>
          </div>
          <div className="overview-progress-track"><i style={{ width: `${(completedSteps / setupItems.length) * 100}%` }} /></div>
          <div className="overview-setup-list">
            {setupItems.map((item) => (
              <button className={`overview-setup-item ${item.done ? "is-done" : ""}`} key={item.key} onClick={() => go(item.key)}>
                <span className="overview-setup-check">{item.done ? <CheckCircle2 size={18} /> : <Circle size={18} />}</span>
                <span className="overview-setup-copy"><b>{item.label}</b><small>{item.detail}</small></span>
                <ChevronRight size={15} />
              </button>
            ))}
          </div>
        </section>
      </div>

      <section className="overview-areas">
        <div className="overview-section-heading overview-areas-heading">
          <div><span className="overview-section-kicker">ONE BUSINESS PLATFORM</span><h3>Start with an area</h3></div>
          <span className="overview-slogan">One business platform.</span>
        </div>
        <div className="overview-area-grid">
          <button className="overview-area-card" onClick={() => go("employees")}><span className="overview-area-icon people"><Users size={18} /></span><span><b>People</b><small>Employees, attendance, leave and payroll.</small></span><ArrowRight size={15} /></button>
          <button className="overview-area-card" onClick={() => go("leads")}><span className="overview-area-icon sales"><BriefcaseBusiness size={18} /></span><span><b>Sales & finance</b><small>Customers, sales and financial workflows.</small></span><ArrowRight size={15} /></button>
          <button className="overview-area-card" onClick={() => go("projects")}><span className="overview-area-icon operations"><Activity size={18} /></span><span><b>Operations</b><small>Projects, service work and automation.</small></span><ArrowRight size={15} /></button>
        </div>
        {localDemo && <p className="overview-integrations-note"><ShieldCheck size={14} /> People and local operations use the local API. ERP posting requires an Odoo service.</p>}
      </section>
    </div>
  );
}
