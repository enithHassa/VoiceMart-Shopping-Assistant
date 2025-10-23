import { useParams, Link } from "react-router-dom";

export default function ProductDetailsPage() {
  const { source, id } = useParams();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Product Details</h1>
      <p>Source: {source}</p>
      <p>ID: {id}</p>

      <Link
        to="/"
        className="inline-block mt-4 text-sm text-blue-600 hover:underline"
      >
        ← Back to search
      </Link>
    </div>
  );
}
