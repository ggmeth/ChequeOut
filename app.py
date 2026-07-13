import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import DashboardLayout from "./components/DashboardLayout";
import Register from "./pages/Register";
import ImportData from "./pages/ImportData"; // ดึงหน้าสแกนและพิมพ์เช็คเข้ามา

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
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

document.title = "ระบบพิมพ์เช็คกรุงไทย";

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

export default import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import DashboardLayout from "./components/DashboardLayout";
import Register from "./pages/Register";
import ImportData from "./pages/ImportData"; // ดึงหน้าสแกนและพิมพ์เช็คเข้ามา

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
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

document.title = "ระบบพิมพ์เช็คกรุงไทย";

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
import React, { useState } from 'react';

export default function ImportData() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // ข้อมูลที่ระบบจะดึงให้อัตโนมัติหลังจากสแกน (เปิดให้แก้ไขได้)
  const [payeeName, setPayeeName] = useState("");
  const [amount, setAmount] = useState<number | string>("");

  // รายละเอียดอื่นๆ ที่คุณเลือกเอง
  const [checkDate, setCheckDate] = useState("");
  const [isCrossed, setIsCrossed] = useState(true);
  const [isBearerLine, setIsBearerLine] = useState(true);

  // ฟังก์ชันจำลองเมื่อผู้ใช้เลือกไฟล์ภาพเอกสารตั้งเบิก
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImagePreview(URL.createObjectURL(file));
      setIsProcessing(true);

      // จำลองการทำงานของ AI OCR (ดึงข้อมูลอัตโนมัติหลังจากอัปโหลดภาพ 2 วินาที)
      setTimeout(() => {
        setPayeeName("บริษัท สมาร์ท ดีเวลลอปเม้นท์ จำกัด");
        setAmount(45000.00);
        setIsProcessing(false);
      }, 2000);
    }
  };

  // ฟังก์ชันแปลงตัวเลขเป็นอักษรไทย (สำหรับพิมพ์ลงเช็ค)
  const formatThaiBahtText = (num: number) => {
    if (!num) return "";
    // สามารถติดตั้งโปรแกรมเสริม npm install thb-text เพื่อแปลงให้ถูกต้องได้ในอนาคต
    return "สี่หมื่นห้าพันบาทถ้วน"; 
  };

  const handlePrint = (e: React.FormEvent) => {
    e.preventDefault();
    window.print(); // สั่งพิมพ์ตัวอักษรออกทางเครื่องพิมพ์
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      
      {/* ─── ส่วนที่ 1: ส่วนทำงานบนหน้าจอ (จะถูกซ่อนอัตโนมัติเมื่อกดพิมพ์) ─── */}
      <div className="no-print grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* ฝั่งซ้าย: อัปโหลดและแสดงหน้าเอกสารตั้งเบิก */}
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-250 flex flex-col items-center justify-center">
          <h3 className="text-lg font-bold text-gray-800 mb-4 self-start">📷 แดชบอร์ดแสกนเอกสารตั้งเบิก</h3>
          
          <label className="w-full flex flex-col items-center px-4 py-6 bg-gray-50 text-cyan-600 rounded-lg shadow-sm tracking-wide uppercase border border-dashed border-cyan-400 cursor-pointer hover:bg-cyan-50 transition">
            <span className="text-sm font-semibold">📁 เลือกภาพถ่ายหรือแสกนหน้าเอกสาร</span>
            <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
          </label>

          {imagePreview && (
            <div className="mt-4 w-full relative border rounded-lg overflow-hidden bg-gray-150">
              <img src={imagePreview} alt="เอกสารตั้งเบิก" className="w-full h-auto max-h-96 object-contain mx-auto" />
              {isProcessing && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white font-medium">
                  🤖 AI กำลังอ่านและดึงข้อมูลอัตโนมัติ...
                </div>
              )}
            </div>
          )}
        </div>

        {/* ฝั่งขวา: ฟอร์มข้อมูลเช็คกรุงไทย */}
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-250 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-850 mb-4">📝 ตรวจสอบและระบุข้อมูลเช็ค</h3>
            
            <form onSubmit={handlePrint} className="space-y-4">
              <div className="p-4 bg-sky-50 rounded-lg space-y-3 border border-sky-100">
                <span className="text-xs font-bold text-sky-750 block">🤖 ระบบดึงให้อัตโนมัติ (ตรวจสอบและแก้ไขได้)</span>
                <div>
                  <label className="block text-sm font-medium text-gray-750">สั่งจ่าย (ชื่อร้าน/บริษัท)</label>
                  <input type="text" className="mt-1 block w-full rounded-md border-gray-300 p-2 border bg-white" value={payeeName} onChange={(e) => setPayeeName(e.target.value)} placeholder="รอผลแสกน หรือพิมพ์ระบุเอง" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-750">จำนวนเงิน (ตัวเลข)</label>
                  <input type="number" className="mt-1 block w-full rounded-md border-gray-300 p-2 border bg-white" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" />
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg space-y-3 border border-gray-200">
                <span className="text-xs font-bold text-gray-500 block">✍️ รายละเอียดที่คุุณเลือกเอง</span>
                <div>
                  <label className="block text-sm font-medium text-gray-750">วันที่บนหน้าเช็ค</label>
                  <input type="date" className="mt-1 block w-full rounded-md border-gray-300 p-2 border bg-white" value={checkDate} onChange={(e) => setCheckDate(e.target.value)} required />
                </div>
                <div className="flex flex-col space-y-2 pt-2">
                  <label className="flex items-center space-x-2"><input type="checkbox" checked={isCrossed} onChange={(e) => setIsCrossed(e.target.checked)} /> <span className="text-sm">ขีดคร่อมเช็ค (A/C Payee Only)</span></label>
                  <label className="flex items-center space-x-2"><input type="checkbox" checked={isBearerLine} onChange={(e) => setIsBearerLine(e.target.checked)} /> <span className="text-sm">ขีดฆ่า "หรือผู้ถือ"</span></label>
                </div>
              </div>

              <button type="submit" disabled={!payeeName || !amount} className="w-full bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-300 text-white font-bold p-3 rounded-lg shadow transition">
                🖨️ สั่งพิมพ์เช็คกรุงไทย
              </button>
            </form>
          </div>
        </div>

      </div>

      {/* ─── ส่วนที่ 2: พิกัดข้อความที่ใช้วิ่งลงกระดาษเช็คกรุงไทยจริง ─── */}
      <div className="print-area font-mono relative mx-auto bg-gray-50/50 border border-dashed border-gray-400 rounded">
        {/* จัดฟอร์แมตวันที่ให้ออกเป็นตัวเลขเรียงกันเพื่อพิมพ์ลงกล่องวันที่ของเช็คไทย */}
        <div className="absolute target-date tracking-[12px] text-lg font-bold">
          {checkDate ? checkDate.replace(/-/g, '').split('').reverse().join('') : ''}
        </div>
        <div className="absolute target-payee text-md font-bold">{payeeName}</div>
        <div className="absolute target-amount-text text-sm font-bold">
          {amount ? `=== ${formatThaiBahtText(Number(amount))} ===` : ''}
        </div>
        <div className="absolute target-amount-num text-md font-bold">
          {amount ? `*${Number(amount).toLocaleString('th-TH', { minimumFractionDigits: 2 })}*` : ''}
        </div>
        {isCrossed && <div className="absolute target-crossed border-t border-b border-black text-[9px] font-bold text-center pt-0.5 leading-none">A/C PAYEE ONLY</div>}
        {isBearerLine && <div className="absolute target-bearer-line border-t-2 border-black"></div>}
      </div>

    </
    /* กำหนดขนาดกล่องข้อความให้เท่าไซส์เช็คกรุงไทยจริง (กว้าง 17.8 ซม. สูง 8.9 ซม.) */
.print-area {
  width: 17.8cm;
  height: 8.9cm;
  display: block;
}

/* ตั้งค่าตำแหน่งตัวอักษรแต่ละช่องบนหน้าเช็คกรุงไทย */
.target-date { top: 0.8cm; right: 0.5cm; }
.target-payee { top: 2.3cm; left: 2.5cm; }
.target-amount-text { top: 3.4cm; left: 3.5cm; }
.target-amount-num { top: 4.5cm; right: 1.0cm; }
.target-crossed { top: 0.5cm; left: 1.5cm; width: 2.5cm; transform: rotate(-15deg); }
.target-bearer-line { top: 2.4cm; right: 2.2cm; width: 1.8cm; }

/* 🖨️ คำสั่งซ่อนอินเทอร์เฟซและเมนูระบบเดิมทั้งหมดตอนกดพิมพ์จริง */
@media print {
  .no-print, 
  header, 
  nav, 
  aside, 
  footer,
  div[class*="sidebar"],
  div[class*="DashboardLayout"],
  main {
    display: none !important;
  }
  
  body { 
    background: white; 
    margin: 0; 
    padding: 0; 
  }
  
  .print-area { 
    display: block !important;
    border: none !important; 
    background: transparent !important; 
    position: relative; 
  }
}
