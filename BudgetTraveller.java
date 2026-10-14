import java.io.*;
import java.util.*;

public class BudgetTraveller {

    static class Edge {
        int u, v, price;
        Edge(int u, int v, int price) {
            this.u = u;
            this.v = v;
            this.price = price;
        }
    }

    static class State implements Comparable<State> {
        int cost, u, stops, coupons;
        State(int cost, int u, int stops, int coupons) {
            this.cost = cost;
            this.u = u;
            this.stops = stops;
            this.coupons = coupons;
        }

        @Override
        public int compareTo(State o) {
            return Integer.compare(this.cost, o.cost);
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            State s = (State) o;
            return u == s.u && stops == s.stops && coupons == s.coupons;
        }

        @Override
        public int hashCode() {
            return Objects.hash(u, stops, coupons);
        }
    }

    static class PathRecord {
        State prev;
        boolean usedCoupon;
        int originalPrice;
        int effectivePrice;

        PathRecord(State prev, boolean usedCoupon, int originalPrice, int effectivePrice) {
            this.prev = prev;
            this.usedCoupon = usedCoupon;
            this.originalPrice = originalPrice;
            this.effectivePrice = effectivePrice;
        }
    }

    public static void main(String[] args) throws IOException {
        Scanner scanner = new Scanner(System.in);
        System.out.println("choose input option:");
        System.out.println("1: console input");
        System.out.println("2: csv input file");
        System.out.println("3: generate random graph");
        int option = scanner.nextInt();

        int n = 0, k = 0, c = 0;
        List<Edge> edges = new ArrayList<>();

        if (option == 1) {
            n = scanner.nextInt();
            int m = scanner.nextInt();
            k = scanner.nextInt();
            c = scanner.nextInt();
            for (int i = 0; i < m; i++) {
                int u = scanner.nextInt();
                int v = scanner.nextInt();
                int p = scanner.nextInt();
                edges.add(new Edge(u, v, p));
            }
        } else if (option == 2) {
            k = scanner.nextInt();
            c = scanner.nextInt();
            System.out.print("csv file path: ");
            String filePath = scanner.next();
            BufferedReader br = new BufferedReader(new FileReader(filePath));
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || !Character.isDigit(line.charAt(0))) continue;
                String[] parts = line.split(",");
                int u = Integer.parseInt(parts[0].trim());
                int v = Integer.parseInt(parts[1].trim());
                int p = Integer.parseInt(parts[2].trim());
                edges.add(new Edge(u, v, p));
                n = Math.max(n, Math.max(u, v));
            }
            br.close();
        } else {
            System.out.print("number of cities N: ");
            n = scanner.nextInt();
            System.out.print("maximum stops K: ");
            k = scanner.nextInt();
            System.out.print("coupons C: ");
            c = scanner.nextInt();
            Random rand = new Random();
            for (int u = 1; u <= n; u++) {
                for (int v = 1; v <= n; v++) {
                    if (u != v && rand.nextDouble() < 0.35) {
                        int price = 1000 + rand.nextInt(9000);
                        edges.add(new Edge(u, v, price));
                    }
                }
            }
        }

        // adjacency list
        Map<Integer, List<Edge>> adj = new HashMap<>();
        for (int i = 1; i <= n; i++) adj.put(i, new ArrayList<>());
        for (Edge e : edges) adj.get(e.u).add(e);

        // distance table & parent pointers
        Map<State, Integer> dist = new HashMap<>();
        Map<State, PathRecord> parent = new HashMap<>();
        PriorityQueue<State> pq = new PriorityQueue<>();

        State startState = new State(0, 1, 0, 0);
        pq.add(startState);
        dist.put(startState, 0);

        int bestCost = -1;
        State endState = null;

        while (!pq.isEmpty()) {
            State curr = pq.poll();

            if (curr.cost > dist.getOrDefault(curr, Integer.MAX_VALUE)) continue;

            if (curr.u == n) {
                bestCost = curr.cost;
                endState = curr;
                break;
            }

            if (curr.stops > k) continue;

            for (Edge e : adj.get(curr.u)) {
                // option 1: without coupon
                int nxtCost = curr.cost + e.price;
                State nxtState = new State(nxtCost, e.v, curr.stops + 1, curr.coupons);
                if (nxtCost < dist.getOrDefault(nxtState, Integer.MAX_VALUE)) {
                    dist.put(nxtState, nxtCost);
                    parent.put(nxtState, new PathRecord(curr, false, e.price, e.price));
                    pq.add(nxtState);
                }

                // option 2: with coupon
                if (curr.coupons < c) {
                    int discCost = curr.cost + (e.price / 2);
                    State nxtStateC = new State(discCost, e.v, curr.stops + 1, curr.coupons + 1);
                    if (discCost < dist.getOrDefault(nxtStateC, Integer.MAX_VALUE)) {
                        dist.put(nxtStateC, discCost);
                        parent.put(nxtStateC, new PathRecord(curr, true, e.price, e.price / 2));
                        pq.add(nxtStateC);
                    }
                }
            }
        }

        System.out.println("output 1: minimum cost = " + bestCost);

        if (bestCost != -1) {
            Set<String> pathEdges = new HashSet<>();
            Map<String, Boolean> couponMap = new HashMap<>();
            State curr = endState;

            while (parent.containsKey(curr)) {
                PathRecord rec = parent.get(curr);
                String key = rec.prev.u + "->" + curr.u + "@" + rec.originalPrice;
                pathEdges.add(key);
                couponMap.put(key, rec.usedCoupon);
                curr = rec.prev;
            }

            FileWriter writer = new FileWriter("path_solution.csv");
            writer.write("u,v,original_price,on_path,coupon_used,effective_price\n");
            for (Edge e : edges) {
                String key = e.u + "->" + e.v + "@" + e.price;
                if (pathEdges.contains(key)) {
                    boolean used = couponMap.get(key);
                    int effPrice = used ? e.price / 2 : e.price;
                    writer.write(e.u + "," + e.v + "," + e.price + ",x," + (used ? "x" : "") + "," + effPrice + "\n");
                } else {
                    writer.write(e.u + "," + e.v + "," + e.price + ",,," + e.price + "\n");
                }
            }
            writer.close();
            System.out.println("output 2: exported path details to path_solution.csv");
        }
    }
}