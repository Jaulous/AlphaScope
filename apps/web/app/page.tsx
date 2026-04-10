import { DashboardShell } from "../components/dashboard-shell";
import { fetchDashboardSnapshotServer, formatDashboardFetchError } from "../lib/api";

export default async function HomePage() {
  try {
    const snapshot = await fetchDashboardSnapshotServer();
    return <DashboardShell initialSnapshot={snapshot} />;
  } catch (error) {
    return <DashboardShell initialError={formatDashboardFetchError(error)} />;
  }
}
