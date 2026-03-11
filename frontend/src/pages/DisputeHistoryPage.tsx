import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { usePersistentProfile } from "@/hooks/usePersistentProfile";
import { MailForMeButton } from "@/components/credits/MailForMeButton";
import { CreditsBalance } from "@/components/credits/CreditsBalance";
import { Loader2, FileText, Eye, Download, History } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface DisputeRecord {
  id: string;
  creditor_name: string | null;
  account_number_masked: string | null;
  bureau: string | null;
  dispute_reason: string | null;
  status: string;
  created_at: string | null;
  letter_text: string | null;
  mailing_address: string;
  lob_id: string | null;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const PAGE_SIZE = 10;

const STATUS_META: Record<string, { label: string; cls: string }> = {
  generated: { label: "Generated", cls: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
  pending:   { label: "Pending",   cls: "bg-amber-500/20 text-amber-300 border-amber-500/30"  },
  sent:      { label: "Mailed",    cls: "bg-blue-500/20 text-blue-300 border-blue-500/30"     },
  resolved:  { label: "Resolved",  cls: "bg-green-500/20 text-green-300 border-green-500/30"  },
  rejected:  { label: "Rejected",  cls: "bg-red-500/20 text-red-300 border-red-500/30"        },
};

const fallbackStatus = { label: "Unknown", cls: "bg-zinc-500/20 text-zinc-300 border-zinc-500/30" };

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return "Date unknown";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function downloadAsTxt(dispute: DisputeRecord) {
  const text = dispute.letter_text
    ?? `Dispute letter for ${dispute.creditor_name ?? "account"} — letter text not available.`;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `dispute-${dispute.creditor_name ?? dispute.id}-${dispute.bureau ?? "bureau"}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── View Letter Modal ────────────────────────────────────────────────────────

function LetterModal({ dispute, onClose }: { dispute: DisputeRecord; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)" }}
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[80vh] flex flex-col rounded-xl border"
        style={{ background: "#111827", borderColor: "#1E2D47" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b" style={{ borderColor: "#1E2D47" }}>
          <div>
            <h2 className="font-semibold text-base">
              {dispute.creditor_name ?? "Dispute Letter"}
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              {dispute.bureau ?? "Bureau unknown"} · {formatDate(dispute.created_at)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors ml-4 shrink-0"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Letter body */}
        <div className="flex-1 overflow-y-auto p-5">
          {dispute.letter_text ? (
            <pre className="whitespace-pre-wrap text-xs leading-relaxed font-mono text-foreground/80">
              {dispute.letter_text}
            </pre>
          ) : (
            <p className="text-muted-foreground text-sm text-center py-8">
              Letter text was not stored for this dispute.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 border-t" style={{ borderColor: "#1E2D47" }}>
          {dispute.letter_text && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => downloadAsTxt(dispute)}
            >
              <Download className="h-3.5 w-3.5 mr-1.5" />
              Download .txt
            </Button>
          )}
          <Button variant="outline" size="sm" className="text-xs" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function DisputeHistoryPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { profile } = usePersistentProfile();

  const [disputes, setDisputes]     = useState<DisputeRecord[]>([]);
  const [isLoading, setIsLoading]   = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [page, setPage]             = useState(1);
  const [viewing, setViewing]       = useState<DisputeRecord | null>(null);

  // ── Fetch ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!user) return;

    const fetchDisputes = async () => {
      const { data, error: fetchErr } = await supabase
        .from("disputes")
        .select("id, creditor_name, account_number_masked, bureau, dispute_reason, status, created_at, letter_text, mailing_address, lob_id")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (fetchErr) {
        console.error("[DisputeHistory] Fetch failed:", fetchErr);
        setError("Failed to load dispute history. Please try again.");
      } else {
        setDisputes(data ?? []);
      }
      setIsLoading(false);
    };

    fetchDisputes();
  }, [user]);

  // ── Pagination ────────────────────────────────────────────────────────────
  const totalPages = Math.max(1, Math.ceil(disputes.length / PAGE_SIZE));
  const paginated  = useMemo(
    () => disputes.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [disputes, page]
  );

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="has-navbar">

      {viewing && <LetterModal dispute={viewing} onClose={() => setViewing(null)} />}

      <div className="container py-12 max-w-4xl mx-auto">
        {/* Page header */}
        <div className="flex items-start justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-1">
              Dispute <span className="text-gold-gradient">History</span>
            </h1>
            <p className="text-muted-foreground text-sm">
              {disputes.length > 0
                ? `${disputes.length} dispute${disputes.length === 1 ? "" : "s"} on record`
                : "Track the status of your submitted credit bureau disputes."}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <CreditsBalance />
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => navigate("/dispute-wizard")}
            >
              <History className="h-3.5 w-3.5 mr-1.5" />
              New Dispute
            </Button>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-[#D4A853]" />
          </div>
        )}

        {/* Error */}
        {!isLoading && error && (
          <div className="text-center py-16">
            <p className="text-muted-foreground">{error}</p>
            <Button variant="outline" size="sm" className="mt-4" onClick={() => window.location.reload()}>
              Try again
            </Button>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && disputes.length === 0 && (
          <div className="text-center py-16">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-40" />
            <p className="text-muted-foreground">No disputes filed yet.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Generate your first dispute letter from the{" "}
              <button
                className="text-[#D4A853] hover:underline"
                onClick={() => navigate("/dispute-wizard")}
              >
                Dispute Wizard
              </button>.
            </p>
          </div>
        )}

        {/* List */}
        {!isLoading && !error && disputes.length > 0 && (
          <>
            <div className="grid gap-3">
              {paginated.map((dispute) => {
                const sm = STATUS_META[dispute.status] ?? fallbackStatus;
                return (
                  <Card key={dispute.id} className="card-midnight">
                    <CardHeader className="pb-3 pt-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <CardTitle className="text-sm font-semibold truncate">
                            {dispute.creditor_name ?? "Unknown creditor"}
                          </CardTitle>
                          <CardDescription className="mt-0.5 text-xs">
                            {dispute.account_number_masked
                              ? `Acct: ${dispute.account_number_masked}`
                              : "No account number"}
                            {dispute.bureau ? ` · ${dispute.bureau}` : ""}
                          </CardDescription>
                        </div>
                        <Badge className={`shrink-0 text-xs border ${sm.cls}`}>
                          {sm.label}
                        </Badge>
                      </div>
                    </CardHeader>

                    <CardContent className="pt-0 pb-4">
                      {dispute.dispute_reason && (
                        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                          {dispute.dispute_reason}
                        </p>
                      )}
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatDate(dispute.created_at)}
                        </span>
                        <div className="flex gap-2">
                          {dispute.letter_text && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs px-2 text-muted-foreground hover:text-foreground"
                              onClick={() => setViewing(dispute)}
                            >
                              <Eye className="h-3.5 w-3.5 mr-1" />
                              View
                            </Button>
                          )}
                          {dispute.letter_text && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs px-2"
                              onClick={() => downloadAsTxt(dispute)}
                            >
                              <Download className="h-3.5 w-3.5 mr-1" />
                              Download
                            </Button>
                          )}
                          {dispute.letter_text && dispute.bureau && (
                            <MailForMeButton
                              disputeId={dispute.id}
                              bureau={dispute.bureau}
                              letterText={dispute.letter_text}
                              fromAddress={{
                                name: `${profile?.first_name ?? ""} ${profile?.last_name ?? ""}`.trim(),
                                address_line1: profile?.address1 ?? "",
                                address_city: profile?.city ?? "",
                                address_state: profile?.state ?? "",
                                address_zip: profile?.zip_code ?? "",
                              }}
                              alreadyMailed={!!dispute.lob_id}
                              onMailed={(letterId) =>
                                setDisputes((prev) =>
                                  prev.map((d) =>
                                    d.id === dispute.id ? { ...d, status: "sent", lob_id: letterId } : d
                                  )
                                )
                              }
                            />
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8">
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        className={page === 1 ? "pointer-events-none opacity-40" : "cursor-pointer"}
                      />
                    </PaginationItem>
                    <PaginationItem>
                      <span className="px-4 text-sm text-muted-foreground">
                        Page {page} of {totalPages}
                      </span>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationNext
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        className={page === totalPages ? "pointer-events-none opacity-40" : "cursor-pointer"}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
