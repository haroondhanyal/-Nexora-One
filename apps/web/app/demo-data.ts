import { modules } from "./modules";
import type { Row, Store } from "./types";

const names=["Ayesha Khan","Hamza Ali","Sara Ahmed","Bilal Raza","Zara Iqbal","Omar Farooq","Hira Malik","Daniyal Shah","Mariam Noor","Usman Tariq","Noor Hassan","Saad Qureshi","Alina Javed","Rehan Siddiqui","Sana Yousaf"];
const companies=["Crescent Retail Group","Northstar Foods","Meridian Supplies","BluePeak Systems","Indus Organics","Urban Loom","Summit Distribution","Vertex Services","Harbor & Co.","Greenline Market","Nova Manufacturing","Beacon Logistics","Craftlane Studio","Silverline Traders","Brightpath Consulting"];
const branches=["Karachi Central","Lahore Gulberg","Islamabad Blue Area","Faisalabad Industrial","Multan Cantt"];
const statuses=["Active","Pending","Approved","In progress","Completed","Draft","Under review","Active","Qualified","Open","Paid","Scheduled","Active","Ready","On hold"];
const titles:Record<string,string[]>={
  leads:["Quarterly supply partnership","New retail rollout","Regional distribution inquiry","ERP modernization proposal","Private label opportunity"],customers:companies,suppliers:["Meridian Office Supplies","PakFresh Produce","Atlas Packaging","Skyline Logistics","Prime Textiles"],sales:["Quotation NX-SO-1042","Retail restock order","Annual service renewal","Store equipment order","Wholesale supply order"],purchasing:["Purchase order NX-208","Packaging replenishment","Branch fixtures","Seasonal inventory order"],inventory:["Organic green tea","Linen table set","Wireless scanner","Premium notebooks","Storage carton pack"],finance:["Customer invoice NX-1042","Supplier bill NX-883","Monthly service invoice","Equipment invoice"],payments:["Bank transfer TX-7421","Card settlement POS-181","Customer remittance RC-408"],budgets:["Marketing · Q4 2026","Operations · FY 2026","People · Q4 2026","Technology · FY 2026"],approvals:["Marketing campaign spend","Supplier onboarding","New branch equipment","Travel reimbursement"],departments:["Operations","Sales","Finance","People & Culture","Customer Experience","Supply Chain","Marketing","Technology"],employees:names,shifts:["Core hours","Morning shift","Evening shift","Warehouse A","Customer support"],attendance:names,leaves:names,payroll:["October 2026 payroll","September 2026 payroll","August 2026 payroll","July 2026 payroll"],payslips:names,storefronts:["Crescent online store","Northstar wholesale","Urban Loom shop"],orders:["Web order NX-3021","Wholesale order NX-3004","Store pickup NX-2987"],promotions:["Autumn launch offer","Team essentials week","Loyal customer reward"],returns:["Return request RT-028","Refund review RT-021","Size exchange RT-016"],pos_sessions:["Register 01 · morning","Register 02 · afternoon","Lahore counter · close"],projects:["Branch experience refresh","Warehouse scan rollout","Customer portal discovery","People operations launch"],timesheets:["Sprint planning and delivery","Branch walkthrough","Monthly close support"],service_tickets:["POS terminal connection","Invoice export question","Stock count discrepancy","Workspace access request"],field_jobs:["Karachi site installation","Lahore network inspection","Faisalabad equipment service"],documents:["Invoice NXO-1042","Purchase order NXO-208","Team handbook sample","Branch opening checklist"],workflows:["Route high-value approvals","Notify team on ticket update","Review new supplier request"],workflow_runs:["Approval workflow · run 018","Ticket assignment · run 024"],reports:["Monthly operations snapshot","Open tickets by branch","Sales order status summary"],custom_fields:["Customer segment","Project region","Supplier rating"],api_clients:["Warehouse integration token","Sales reporting client","Finance export client"],integration_health:["Local API service","Odoo connector","Email delivery","File storage"],imports:["October customer list","Opening inventory batch","Supplier catalog update"],roles:["Owner","Admin","Finance manager","HR manager","Sales","Purchasing","Warehouse","Employee","Staff","Auditor"]
};
function periodDate(index:number,end=false):string{
 const date=new Date();
 date.setUTCHours(0,0,0,0);
 date.setUTCDate(1);
 date.setUTCMonth(date.getUTCMonth()-(index%9)+(end?1:0));
 if(end)date.setUTCDate(0);
 return date.toISOString().slice(0,10);
}
function valueFor(kind:string,col:string,index:number):string{
 const person=names[index%names.length], company=companies[(index+3)%companies.length], branch=branches[index%branches.length], status=statuses[index%statuses.length];
 if(["Status","Stage"].includes(col))return kind==="leads"?["New","Qualified","Proposal","Qualified","Won"][index%5]:status;
 if(col==="Branch"||col==="Branch name")return branch;
 if(col==="Name"&&kind==="departments")return ["Operations","Sales","Finance","People & Culture","Customer Experience","Supply Chain","Marketing","Technology"][index%8];
 if(col==="Name"||col==="Employee"||col==="Owner"||col==="Assignee"||col==="Technician"||col==="Requested by"||col==="Approver")return person;
 if(col==="Email")return `${person.toLowerCase().replaceAll(" ",".")}@example.test`;
 if(col==="Customer"||col==="Company"||col==="Party")return company;
 if(col==="Supplier")return ["Meridian Office Supplies","PakFresh Produce","Atlas Packaging","Skyline Logistics","Prime Textiles"][index%5];
 if(col==="Product")return ["Organic green tea","Linen table set","Wireless scanner","Premium notebooks","Storage carton pack"][index%5];
 if(col==="Phone")return `+92 3${(index%4)+1}00 555 ${String(1000+index)}`;
 if(col==="Date"||col==="Work date"||col==="Hire date"||col==="Start date"||col==="End date"||col==="Due date"||col==="Expected"||col==="Scheduled date"||col==="Last event")return new Date(Date.now()-index*86400000).toISOString().slice(0,10);
 if(col==="Period start")return periodDate(index);
 if(col==="Period end")return periodDate(index,true);
 if(col==="Title"||col==="Lead"||col==="Request"||col==="Document"||col==="Purchase order"||col==="Budget"||col==="Reference"||col==="Project"||col==="Register"||col==="Record")return `${(titles[kind]||[kind])[index%(titles[kind]||[kind]).length]}${index>=((titles[kind]||[kind]).length)?` · ${String(index+1).padStart(2,"0")}`:""}`;
 if(col==="Role")return ["Owner","Admin","Sales","Finance manager","HR manager","Staff"][index%6];
 if(col==="Role name")return (titles.roles||[])[index%10];
 if(col==="Permissions")return ["Workspace · settings · members","Finance · payments · budgets","People · payroll · attendance","Sales · CRM · customers","Inventory · purchasing"][index%5];
 if(col==="Industry")return ["Retail","Distribution","Manufacturing","Professional services","E-commerce"][index%5];
 if(col==="City")return ["Karachi","Lahore","Islamabad","Faisalabad","Multan"][index%5];
 if(col==="Timezone")return "Asia/Karachi";
 if(col==="Document type")return ["Customer invoice","Supplier bill","Policy","Checklist"][index%4];
 if(col==="File name")return ["invoice-nxo-1042.pdf","purchase-order-nxo-208.pdf","team-handbook-sample.pdf"][index%3];
 if(col==="Description")return ["Illustrative workspace demo record.","For product walkthrough only.","Sample data · no real transaction."][index%3];
 if(col==="Domain")return `${kind}-${index+1}.demo.nexora.local`;
 if(col==="Currency")return "PKR";
 if(col==="Reason")return ["Annual leave","Customer request","Quarterly planning","Service inspection"][index%4];
 if(col==="Priority")return ["High","Normal","Urgent","Low"][index%4];
 if(col==="Action")return kind==="workflows"?["set_status","create_approval"][index%2]:["workspace.created","record.updated","document.uploaded"][index%3];
 if(col==="Target status")return ["approved","in_progress","closed","active"][index%4];
 if(col==="Target kind")return ["orders","projects","service_tickets","documents"][index%4];
 if(col==="Entity")return ["projects","orders","documents","service_tickets"][index%4];
 if(col==="Field type")return ["text","number","date","boolean"][index%4];
 if(col==="Required")return index%2?"No":"Yes";
 if(col==="Source"&&kind==="attendance")return ["Web","Mobile","Manual","Device"][index%4];
 if(col==="Source kind"||col==="Source")return ["orders","projects","service_tickets","field_jobs"][index%4];
 if(col==="Group by")return index%2?"branch":"status";
 if(col==="Connector")return ["Odoo","SMTP","Local API","Object storage"][index%4];
 if(col==="Last run")return `${new Date(Date.now()-index*3600000).toISOString().slice(0,16).replace("T"," ")} UTC`;
 if(col==="Records")return String(12+index*3);
 if(col==="Payslip count")return "15";
 if(col==="Base pay")return (85000+index*4500).toLocaleString("en-PK");
 if(col==="Amount"||col==="Total"||col==="Value"||col==="Budget"||col==="Spent"||col==="Limit"||col==="Net pay"||col==="Opening cash"||col==="Closing cash"||col==="Cash sales"||col==="Expected close"||col==="Variance"||col==="Sale price"||col==="Cost")return (18000+index*7250).toLocaleString("en-PK");
 if(col==="Quantity"||col==="On hand"||col==="Reorder at"||col==="Hours"||col==="Days"||col==="Discount")return String(4+index*2);
 if(col==="SKU")return `NX-${String(2400+index)}`;
 if(col==="Location")return branch;
 if(col==="Customer")return company;
 if(col==="Contact")return person;
 if(col==="Credit status")return ["Active","Review","Active","On hold"][index%4];
 if(col==="Delivery")return ["Ready","In progress","Pending"][index%3];
 if(col==="Department")return ["Operations","Sales","Finance","People & Culture"][index%4];
 if(col==="Job title")return ["Operations lead","Account executive","Finance analyst","People partner","Service specialist"][index%5];
 if(col==="Shift")return ["Core hours","Morning shift","Evening shift"][index%3];
 if(col==="Employee no")return `NX-${String(1001+index)}`;
 if(col==="Date")return new Date(Date.now()-index*86400000).toISOString().slice(0,10);
 return `${col} ${index+1}`;
}
export function createDemoStore():Store{
 const store:Store={};
 for(const definition of modules){
  if(["overview","settings","assistant"].includes(definition.key))continue;
  const count=12;
  store[definition.key]=Array.from({length:count},(_,index)=>{
   const row:Row={id:`demo-${definition.key}-${String(index+1).padStart(2,"0")}`,version:"1",odoo_id:""};
   for(const col of definition.columns)row[col]=valueFor(definition.key,col,index);
   if(definition.key==="documents")row["Demo URL"]=`/demo-documents/${["invoice-nxo-1042.pdf","purchase-order-nxo-208.pdf","team-handbook-sample.pdf"][index%3]}`;
   return row;
  });
 }
 return store;
}
export function loadDemoStore():Store{
 const defaults=createDemoStore();
 try{
  const saved=localStorage.getItem("nexora-demo-records");
  if(!saved){saveDemoStore(defaults);return defaults;}
  const parsed=JSON.parse(saved) as Store;
  return Object.fromEntries(Object.entries(defaults).map(([key,rows])=>[key,Array.isArray(parsed[key])&&parsed[key].length?parsed[key]:rows]));
 }catch{return defaults}
}
export function saveDemoStore(store:Store){try{localStorage.setItem("nexora-demo-records",JSON.stringify(store))}catch{/* Browser storage may be disabled. */}}

export function padDemoRows(kind:string,records:Row[],minimum=12):Row[]{
 const examples=loadDemoStore()[kind]||[];
 if(records.length>=minimum)return records;
 const remainder=examples.filter(sample=>!records.some(record=>record.id===sample.id)).slice(0,minimum-records.length);
 return [...records,...remainder];
}
