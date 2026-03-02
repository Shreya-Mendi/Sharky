"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchDeals, fetchIndustries } from "@/lib/api";
import type { Deal, Industry } from "@/lib/api";
import DealsFilters from "@/components/deals/DealsFilters";
import DealsTable from "@/components/deals/DealsTable";

const PAGE_SIZE = 25;

export default function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [filters, setFilters] = useState({
    industry: "",
    has_deal: undefined as boolean | undefined,
    search: "",
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIndustries().then(setIndustries);
  }, []);

  const loadDeals = useCallback(() => {
    setLoading(true);
    fetchDeals({
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      industry: filters.industry || undefined,
      has_deal: filters.has_deal,
      search: filters.search || undefined,
    }).then(({ deals, total }) => {
      setDeals(deals);
      setTotal(total);
      setLoading(false);
    });
  }, [page, filters]);

  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  return (
    <div className="space-y-6">
      <DealsFilters
        filters={filters}
        onChange={(f) => {
          setFilters(f);
          setPage(0);
        }}
        industries={industries}
      />
      <DealsTable
        deals={deals}
        total={total}
        page={page}
        onPageChange={setPage}
        loading={loading}
      />
    </div>
  );
}
