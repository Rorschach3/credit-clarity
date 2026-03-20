import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import { usePersistentProfile } from "@/hooks/usePersistentProfile";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileText, Upload, History, User, AlertTriangle,
  CheckCircle2, Clock, ArrowRight, Shield
} from "lucide-react";

interface DashboardStats {
  tradelineCount: number;
  negativeCount: number;
  disputeCount: number;
  resolvedCount: number;
}

interface RecentDispute {
  id: string;
  creditor_name: string | null;
  bureau: string | null;
  status: string;
  created_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  generated: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  pending:   "bg-amber-500/20 text-amber-300 border-amber-500/30",
  sent:      "bg-blue-500/20 text-blue-300 border-blue-500/30",
  resolved:  "bg-green-500/20 text-green-300 border-green-500/30",
  rejected:  "bg-red-500/20 text-red-300 border-red-500/30",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { disputeProfile, isProfileComplete, missingFields } = usePersistentProfile();
  const [stats, setStats] = useState<DashboardStats>({ tradelineCount: 0, negativeCount: 0, disputeCount: 0, resolvedCount: 0 });
  const [recentDisputes, setRecentDisputes] = useState<RecentDispute[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.id) return;
    let cancelled = false;

    const load = async () => {
      const [tradelinesRes, disputesRes] = await Promise.allSettled([
        supabase.from("tradelines").select("id, is_negative").eq("user_id", user.id),
        supabase.from("disputes").select("id, creditor_name, bureau, status, created_at")
          .eq("user_id", user.id).order("created_at", { ascending: false }).limit(5),
      ]);

      if (cancelled) return;

      const tradelines = tradelinesRes.status === "fulfilled" ? tradelinesRes.value.data ?? [] : [];
      const disputes = disputesRes.status === "fulfilled" ? disputesRes.value.data ?? [] : [];

      setStats({
        tradelineCount: tradelines.length,
        negativeCount: tradelines.filter((t: any) => t.is_negative).length,
        disputeCount: disputes.length,
        resolvedCount: disputes.filter((d: any) => d.status === "resolved").length,
      });
      setRecentDisputes(disputes as RecentDispute[]);
      setLoading(false);
    };

    load();
    return () => { cancelled = true; };
  }, [user?.id]);

  const firstName = disputeProfile?.firstName ?? user?.email?.split("@")[0] ?? "there";

  return (
    <div className="has-navbar min-h-screen bg-background text-foreground">
      <div className="container max-w-5xl mx-auto py-10 px-4 space-y-8">

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">
            Welcome back, <span className="text-gold-gradient">{firstName}</span>
          </h1>
          <p className="text-muted-foreground mt-1">Here's your credit repair overview.</p>
        </div>

        {/* Profile completion gate */}
        {!isProfileComplete && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-amber-200">Complete your profile to start disputing</p>
              <p className="text-sm text-amber-300/70 mt-0.5">
                Missing: {missingFields.map(f => f.replace(/_/g, " ")).join(", ")}
              </p>
            </div>
            <Button onClick={() => navigate("/profile")} className="btn-gold flex-shrink-0">
              Complete Profile
            </Button>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Tradelines", value: loading ? "—" : stats.tradelineCount, icon: FileText, color: "text-blue-400" },
            { label: "Negative Items", value: loading ? "—" : stats.negativeCount, icon: AlertTriangle, color: "text-red-400" },
            { label: "Disputes Filed", value: loading ? "—" : stats.disputeCount, icon: Shield, color: "text-purple-400" },
            { label: "Resolved", value: loading ? "—" : stats.resolvedCount, icon: CheckCircle2, color: "text-green-400" },
          ].map(({ label, value, icon: Icon, color }) => (
            <Card key={label} className="card-midnight">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">{label}</span>
                  <Icon className={`h-4 w-4 ${color}`} />
                </div>
                <div className="text-2xl font-bold">
                  {typeof value === 'number' ? (
                    <AnimatedNumber value={value} />
                  ) : (
                    value
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Link to="/credit-report-upload" className="group">
              <Card className="card-midnight h-full hover:border-[#D4A853]/40 transition-colors transition-transform duration-150 ease-in-out group-hover:scale-[1.02]">
                <CardContent className="p-5 flex items-center gap-3">
                  <div className="rounded-full bg-blue-500/10 p-2">
                    <Upload className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Upload Report</p>
                    <p className="text-xs text-muted-foreground">Extract tradelines from PDF</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>

            <Link to="/dispute-wizard" className="group">
              <Card className="card-midnight h-full hover:border-[#D4A853]/40 transition-colors transition-transform duration-150 ease-in-out group-hover:scale-[1.02]">
                <CardContent className="p-5 flex items-center gap-3">
                  <div className="rounded-full bg-[#D4A853]/10 p-2">
                    <FileText className="h-5 w-5 text-[#D4A853]" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Generate Dispute</p>
                    <p className="text-xs text-muted-foreground">Create FCRA dispute letters</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>

            <Link to="/dispute-history" className="group">
              <Card className="card-midnight h-full hover:border-[#D4A853]/40 transition-colors transition-transform duration-150 ease-in-out group-hover:scale-[1.02]">
                <CardContent className="p-5 flex items-center gap-3">
                  <div className="rounded-full bg-purple-500/10 p-2">
                    <History className="h-5 w-5 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Dispute History</p>
                    <p className="text-xs text-muted-foreground">View past letters</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>

        {/* Recent Disputes */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Recent Disputes</h2>
            <Link to="/dispute-history" className="text-sm text-[#D4A853] hover:underline">
              View all
            </Link>
          </div>

          {loading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 rounded-lg bg-white/5 animate-pulse" />
              ))}
            </div>
          ) : recentDisputes.length === 0 ? (
            <Card className="card-midnight">
              <CardContent className="p-8 text-center">
                <Shield className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No disputes yet.</p>
                <Button onClick={() => navigate("/dispute-wizard")} className="btn-gold mt-4">
                  Start Your First Dispute
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {recentDisputes.map(d => (
                <Card key={d.id} className="card-midnight hover:bg-background/20 transition-colors">
                  <CardContent className="p-4 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium truncate">{d.creditor_name ?? "Unknown creditor"}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {d.bureau ?? "—"} &middot; {d.created_at ? new Date(d.created_at).toLocaleDateString() : "—"}
                      </p>
                    </div>
                    <Badge className={`text-xs border ${STATUS_COLORS[d.status] ?? STATUS_COLORS.pending} flex-shrink-0`}>
                      {d.status}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Profile CTA if complete */}
        {isProfileComplete && (
          <Card className="card-midnight border-[#D4A853]/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-4 w-4 text-[#D4A853]" />
                Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {disputeProfile?.address1}, {disputeProfile?.city}, {disputeProfile?.state}
              </p>
              <Button variant="outline" size="sm" onClick={() => navigate("/profile")}
                className="border-white/10 hover:bg-white/5">
                Edit <Clock className="ml-1 h-3.5 w-3.5" />
              </Button>
            </CardContent>
          </Card>
        )}

      </div>
    </div>
  );
}
