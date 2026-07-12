import React, { useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import DashboardLayout from "./components/DashboardLayout";
import Register from "./pages/Register";

// ==========================================
// 1. หน้าพิมพ์เช็คที่เราสร้างขึ้นมาไว้ตรงนี้เลย
// ==========================================
function ImportData() {
  // จำลองข้อมูลจาก AI OCR (แก้ไขได้)
  const [payeeName, setPayeeName] = useState("บริษัท สมาร์ท ดีเวลลอปเม้นท์ จำกัด");
  const [amount, setAmount] = useState(45000.00);
  
  // ข้อมูลที่คุณเลือกเอง
  const [chequeDate, setChequeDate] = useState(""); 
  const [isCrossed, setIsCrossed] = useState(true); 
  const [isDeleteOrBearer, setIsDeleteOrBearer] = useState(true); 

  const formatThaiBahtText = (num: number) => {
    return "สี่หมื่นห้าพันบาทถ้วน"; // อนาคตใช้ library แปลงอัตโนมัติ
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* ฟอร์มจัดการข้อมูล (จะถูกซ่อนตอนสั่งพิมพ์) */}
      <div className="no-print bg-white p-6 rounded-xl shadow-md border border-gray-250">
        <h2 className="text-xl font-bold text-gray-850 mb-4">🖨️ ระบบพิมพ์เช็คธนาคารกรุงไทย</h2>
        <form onSubmit={(e) => { e.preventDefault(); window.print(); }} className="space-y-4">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-sky-50 rounded-lg border border-sky-100">
            <div className="col-span-2"><span className="text-xs font-bold text-sky-750 block">🤖 ข้อมูลที่ระบบดึงให้อัตโนมัติ (แก้ไขได้)</span></div>
            <div>
              <label className="block text-sm font-medium text-gray-750">สั่งจ่าย (ชื่อร้าน/บริษัท)</label>
              <input type="text" className="mt-1 block w-full rounded-md border-gray-300 p-2 border bg-white" value={payeeName} onChange={(e) => setPayeeName(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-750">จำนวนเงิน (ตัวเลข)</label>
              <input type="number" className="mt-1 block w-full rounded-md border-gray-300 p-2 border bg-white" value={amount} onChange={(e) => setAmount(Number(e.target.value))} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="col-span-2"><span className="text-xs font-bold text-gray-500 block">✍️ คุณระบุเอง</span></div>
            <div>
              <label className="block text-sm font-medium text-gray-750">วันที่บนหน้าเช็ค</label>
              <input type="date" className="mt-1 block w-full rounded-md border-gray-300 p-2 border bg-white" value={chequeDate} onChange={(e) => setCheckDate(e.target.value)} required />
            </div>
            <div className="flex flex-col justify-center space-y-2 pt-4">
              <label className="flex items-center space-x-2"><input type="checkbox" checked={isCrossed} onChange={(e) => setIsCrossed(e.target.checked)} /> <span className="text-sm">ขีดคร่อมเช็ค (A/C Payee Only)</span></label>
              <label className="flex items-center space-x-2"><input type="checkbox" checked={isDeleteOrBearer} onChange={(e) => setIsDeleteOrBearer(e.target.checked)} /> <span className="text-sm">ขีดฆ่า "หรือผู้ถือ"</span></label>
            </div>
          </div>
          <button type="submit" className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-bold p-3 rounded-lg shadow">🖨️ สั่งพิมพ์เช็คกรุงไทย</button>
        </form>
      </div>

      {/* พิกัดข้อความบนหน้าเช็คจริง */}
      <div className="print-area font-mono relative mx-auto bg-gray-50 border border-dashed border-gray-400 rounded">
        <div className="absolute target-date tracking-[12px] text-lg font-bold">{chequeDate ? chequeDate.replace(/-/g, '').split('').reverse().join('') : ''}</div>
        <div className="absolute target-payee text-md font-bold">{payeeName}</div>
        <div className="absolute target-amount-text text-sm font-bold">{`=== ${formatThaiBahtText(amount)} ===`}</div>
        <div className="absolute target-amount-num text-md font-bold">{`*${amount.toLocaleString('th-TH', { minimumFractionDigits: 2 })}*`}</div>
        {isCrossed && <div className="absolute target-crossed border-t border-b border-black text-[9px] font-bold text-center pt-0.5 leading-none">A/C PAYEE ONLY</div>}
        {isDeleteOrBearer && <div className="absolute target-bearer-line border-t border-black"></div>}
      </div>
    </div>
  );
}

// ==========================================
// 2. ส่วน Router ควบคุมเส้นทาง
// ==========================================
function PrivatePage({ children }: { children: React.ReactNode }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}

function Router() {
  return (
    <Switch>
      <Route path="/">{() => <PrivatePage><Home /></PrivatePage>}</Route>
      <Route path="/register">{() => <PrivatePage><Register /></PrivatePage>}</Route>
      <Route path="/import">{() => <PrivatePage><ImportData /></PrivatePage>}</Route>
      <Route path={"/404"} component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

// ==========================================
// 3. ฟังก์ชันหลักของระบบ
// ==========================================
function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
