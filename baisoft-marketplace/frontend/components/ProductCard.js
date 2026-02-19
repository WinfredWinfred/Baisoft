import { memo } from 'react';
import Link from 'next/link';

/**
 * Memoized Product Card Component
 * Prevents unnecessary re-renders when parent component updates
 * 
 * @param {Object} product - Product data
 * @param {boolean} showBusiness - Whether to show business name
 */
const ProductCard = memo(({ product, showBusiness = true }) => {
  return (
    <div 
      className="group bg-white rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-200"
      data-testid={`product-card-${product.id}`}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900 group-hover:text-blue-900 transition-colors">
              {product.name}
            </h3>
            {showBusiness && product.business?.name && (
              <p className="mt-1 text-xs text-gray-500 uppercase tracking-wide font-medium">
                {product.business.name}
              </p>
            )}
          </div>
        </div>
        
        <p className="text-sm text-gray-600 leading-relaxed mb-4 line-clamp-3">
          {product.description}
        </p>
        
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div>
            <p className="text-2xl font-bold text-blue-900" aria-label={`Price: $${parseFloat(product.price || 0).toFixed(2)}`}>
              ${parseFloat(product.price || 0).toFixed(2)}
            </p>
          </div>
          <Link
            href={`/products/${product.id}`}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-900 rounded-lg hover:bg-blue-800 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-900"
            aria-label={`View details for ${product.name}`}
          >
            View Details
            <svg className="ml-2 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
});

ProductCard.displayName = 'ProductCard';

export default ProductCard;
