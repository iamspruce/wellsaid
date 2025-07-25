// File: pages/Home.tsx
import ContentArea from "../components/layout/ContentArea";

/**
 * Represents the Home page of the application.
 * It uses the centralized EditorContext (indirectly via ContentArea).
 */
const Home = () => {
  return (
    <div className="h-full">
      <ContentArea shouldAnalyze={true} />
    </div>
  );
};

export default Home;
