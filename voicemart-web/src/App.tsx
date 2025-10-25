import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import HomePage from "./pages/HomePage";
import ProductDetailsPage from "./pages/ProductDetailsPage";
import SignupPage from "./pages/SignupPage";
import LoginPage from "./pages/LoginPage";
import { useAuthStore } from "./lib/auth-store";
import { isAuthenticated } from "./lib/storage";

function App() {
  const { isAuthenticated: isAuth } = useAuthStore();
  const isLoggedIn = isAuth || isAuthenticated();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route element={<MainLayout />}>
          <Route 
            path="/" 
            element={isLoggedIn ? <HomePage /> : <Navigate to="/login" replace />} 
          />
          <Route 
            path="/product/:source/:id" 
            element={isLoggedIn ? <ProductDetailsPage /> : <Navigate to="/login" replace />} 
          />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
