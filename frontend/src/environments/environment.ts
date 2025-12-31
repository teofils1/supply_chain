/**
 * Environment configuration for development
 */
export const environment = {
  production: false,
  apiUrl: '/api',

  // Pagination settings
  pagination: {
    defaultPageSize: 5,
    pageSizeOptions: [5, 10, 25, 50, 100],
  },

  // Cache settings (in milliseconds)
  cache: {
    defaultTtl: 60000, // 1 minute
    productsTtl: 60000,
    batchesTtl: 30000,
    packsTtl: 30000,
    shipmentsTtl: 30000,
    eventsTtl: 60000,
  },
};
