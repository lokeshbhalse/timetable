// frontend/src/components/StarBackground.tsx
import { useMemo } from "react";

const StarBackground = () => {
  const stars = useMemo(() => {
    return Array.from({ length: 150 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 4 + 2,
      delay: Math.random() * 5,
    }));
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <div className="absolute inset-0" style={{ background: "radial-gradient(circle at center, #0a0a2a 0%, #1a1a3a 100%)" }} />
      
      <div className="absolute w-96 h-96 rounded-full opacity-20 blur-3xl"
        style={{ background: "hsl(260 70% 50%)", top: "10%", right: "10%" }} />
      <div className="absolute w-80 h-80 rounded-full opacity-15 blur-3xl"
        style={{ background: "hsl(200 80% 50%)", bottom: "20%", left: "5%" }} />
      <div className="absolute w-64 h-64 rounded-full opacity-10 blur-3xl"
        style={{ background: "hsl(320 60% 50%)", top: "50%", left: "50%" }} />

      {stars.map(star => (
        <div
          key={star.id}
          className="star"
          style={{
            left: `${star.left}%`,
            top: `${star.top}%`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            animationDuration: `${star.duration}s`,
            animationDelay: `${star.delay}s`,
          }}
        />
      ))}
    </div>
  );
};

export default StarBackground;