import { useParams, Link } from "react-router-dom";
import { useProductDetails } from "../lib/hooks";
export default function ProductDetailsPage() {
  const { id } = useParams();
  const { product, loading, error } = useProductDetails(id || '');

  if (loading) return <div>Loading details…</div>;
  if (error) return <div>❌ Failed to load product details: {error}</div>;

  if (!product)
    return (
      <div>
        <p className="text-gray-500">No details found.</p>
        <Link to="/" className="text-blue-600 underline">← Back</Link>
      </div>
    );

  return (
    <div className="space-y-6">
      <Link to="/" className="text-blue-600 hover:underline text-sm">← Back to results</Link>

      <div className="flex flex-col md:flex-row gap-8 bg-white border rounded-xl p-6">
        <div className="md:w-1/3">
          {product.image_url && (
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full rounded-lg object-cover"
            />
          )}
        </div>

        <div className="flex-1 space-y-4">
          <h1 className="text-2xl font-semibold">{product.title}</h1>
          <div className="text-xl font-bold text-green-700">
            {product.currency} {product.price.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Source: {product.source}</div>
          <p className="text-gray-700">{product.description}</p>


          {product.url && (
            <a
              href={product.url}
              target="_blank"
              rel="noreferrer"
              className="inline-block mt-4 px-4 py-2 rounded-lg bg-black text-white"
            >
              View on {product.source}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
