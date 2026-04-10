// frontend/src/pages/NotFound.tsx
import { useLocation } from "react-router-dom";

const NotFound = () => {
  const location = useLocation();

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="text-center">
        <h1 className="mb-4 text-6xl font-bold text-white">404</h1>
        <p className="mb-4 text-xl text-gray-400">Oops! Page not found</p>
        <p className="text-gray-500">The page "{location.pathname}" does not exist.</p>
        <a href="/" className="mt-4 inline-block px-6 py-2 rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition">
          Return to Home
        </a>
      </div>
    </div>
  );
};

export default NotFound;