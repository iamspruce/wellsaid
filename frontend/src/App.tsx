import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import Home from "./pages/Home";
import ParaphraserPage from "./pages/ParaphraserPage";
import { EditorProvider } from "./context/EditorContext";
import { Toaster as Sonner, type ToasterProps } from "sonner";

function App() {
  return (
    <BrowserRouter>
      <EditorProvider>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/paraphraser" element={<ParaphraserPage />} />
          </Routes>
          <Sonner />
        </AppLayout>
      </EditorProvider>
    </BrowserRouter>
  );
}

export default App;
