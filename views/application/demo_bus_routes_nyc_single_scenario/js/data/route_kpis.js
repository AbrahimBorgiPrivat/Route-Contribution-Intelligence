import { fmt, fmtKr } from "../utils/fmt.js";

export function extractRouteKPIs(routeData) {

    const sols = routeData.solutions || [];
    const t1 = sols.find(s => s.strict_order);
    const t2 = sols.find(s => !s.strict_order);
    
    return {
        route_id: routeData.route_id,
        profile: t1?.profile?.profile ?? "-",
        t1_L_original: fmt(t1?.L_original, t1?.profile?.unit ?? "", 0, "min"),
        t1_L_opt: fmt(t1?.L_opt, t1?.profile?.unit ?? "", 0, "min"),
        t1_DG_original: fmtKr(t1?.DG_original,0) ?? "-",
        t1_DG_best: fmtKr(t1?.DG_best,0)  ?? "-",
        t1_seg_outliers: (t1?.S_outlier || []).length,
        t2_L_original: fmt(t2?.L_original, t2?.profile?.unit ?? "", 0, "min"),
        t2_L_opt: fmt(t2?.L_opt, t2?.profile?.unit ?? "", 0, "min"),
        t2_DG_original: fmtKr(t2?.DG_original,0) ?? "-",
        t2_DG_best: fmtKr(t2?.DG_best,0) ?? "-",
        t2_seg_outliers: (t2?.S_outlier || []).length
    };
}
