
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Scanner;

/**
 * Paddy Mitra - an offline-first console MVP for Karnataka paddy farmers.
 *
 * This version provides the rules and content layer that can later be connected
 * to a Flutter app, a disease model, weather APIs, and ESP32 sensor telemetry.
 */
public class samrt_agr_ {

    private static final Scanner INPUT = new Scanner(System.in);

    private static final Map<String, DistrictProfile> DISTRICTS = new LinkedHashMap<>();
    private static final Map<String, Advisory> ADVISORIES = new LinkedHashMap<>();

    static {
        DISTRICTS.put("Mandya", new DistrictProfile(
                "Mandya", "South Karnataka", "May-June", "June-July", "October-November"));
        DISTRICTS.put("Raichur", new DistrictProfile(
                "Raichur", "North Karnataka", "June", "June-July", "October-November"));
        DISTRICTS.put("Koppal", new DistrictProfile(
                "Koppal", "North Karnataka", "June", "June-July", "October-November"));
        DISTRICTS.put("Shivamogga", new DistrictProfile(
                "Shivamogga", "Malnad Karnataka", "May-June", "June-July", "October-November"));

        ADVISORIES.put("leaf blast", new Advisory(
                "Leaf Blast", "Spindle-shaped grey or brown lesions on leaves.",
                "Scout after cloudy, wet weather; avoid excess nitrogen.",
                "Ask a local agronomist for a registered fungicide and label dose per acre.",
                "Remove heavily infected leaves where practical and improve field airflow."));
        ADVISORIES.put("neck blast", new Advisory(
                "Neck Blast", "Dark lesions around the neck of the panicle causing empty grains.",
                "Protect the crop around booting and flowering; do not allow water stress.",
                "Use only a locally registered fungicide at the label dose and observe the pre-harvest interval.",
                "Use certified seed and balanced nutrition in the next crop."));
        ADVISORIES.put("brown spot", new Advisory(
                "Brown Spot", "Round brown spots with a lighter centre on leaves or grains.",
                "Check drainage and crop nutrition, especially potassium.",
                "Use a registered seed or foliar treatment after expert confirmation.",
                "Use clean seed, compost, and balanced fertilisation."));
        ADVISORIES.put("sheath blight", new Advisory(
                "Sheath Blight", "Oval green-grey lesions spreading from the water line on sheaths.",
                "Avoid dense canopy and unnecessary standing water.",
                "Ask an agronomist to confirm the product and dose per acre before spraying.",
                "Improve spacing and remove volunteer plants where feasible."));
        ADVISORIES.put("false smut", new Advisory(
                "False Smut", "Yellow-orange to green powdery balls replacing individual grains.",
                "Scout at booting and flowering, especially after humid weather.",
                "Use a registered fungicide only after diagnosis and follow the label.",
                "Use clean seed and field sanitation."));
        ADVISORIES.put("stem borer", new Advisory(
                "Stem Borer", "Dead hearts in young plants or white heads in older plants.",
                "Inspect tillers weekly and check for egg masses.",
                "Use an integrated pest-management recommendation from an agronomist; never exceed the label dose.",
                "Use pheromone traps and remove affected tillers."));
        ADVISORIES.put("leaf folder", new Advisory(
                "Leaf Folder", "Leaves folded lengthwise with scraped or whitish tissue.",
                "Avoid excessive nitrogen and scout the inner canopy.",
                "Choose a locally registered treatment only after confirming economic threshold.",
                "Encourage natural enemies and remove folded leaves during early attack."));
        ADVISORIES.put("hopper", new Advisory(
                "Hopper", "Yellowing, hopper burn, or insects at the base of tillers.",
                "Do not continuously flood; inspect the crop base and avoid broad-spectrum sprays.",
                "Get expert confirmation before treatment because resistance is common.",
                "Use light traps and preserve spiders and other beneficial insects."));
    }

    public static void main(String[] args) {
        System.out.println("\n=== Paddy Mitra | Karnataka Paddy Assistant ===");
        System.out.println("Offline MVP: calendar, irrigation rules, and crop-health advisories.\n");

        boolean running = true;
        while (running) {
            System.out.println("1. District-wise crop calendar");
            System.out.println("2. Irrigation recommendation");
            System.out.println("3. Disease / pest advisory");
            System.out.println("4. Smart water-level decision");
            System.out.println("5. Exit");
            int choice = readInt("Choose an option: ", 1, 5);

            switch (choice) {
                case 1 ->
                    showCalendar();
                case 2 ->
                    showIrrigationPlan();
                case 3 ->
                    showHealthAdvisory();
                case 4 ->
                    showWaterDecision();
                default -> {
                    running = false;
                    System.out.println("Stay safe in the field. Paddy Mitra will see you next time!");
                }
            }
            System.out.println();
        }
    }

    private static void showCalendar() {
        DistrictProfile district = chooseDistrict();
        String season = chooseSeason();
        System.out.println("\n--- " + district.name + " " + season + " calendar ---");
        System.out.println("Agro-climate zone: " + district.zone);
        System.out.println("Nursery: " + district.nursery);
        System.out.println("Transplanting: " + district.transplanting);
        System.out.println("Expected harvest: " + district.harvest);
        System.out.println("Tip / ಸಲಹೆ: Keep a 10-day harvest drainage window in your plan.");
        if (season.equals("Summer")) {
            System.out.println("Summer alert: confirm canal or borewell availability before planting.");
        } else {
            System.out.println("Kharif alert: plan drainage and spraying around rainfall forecasts.");
        }
    }

    private static void showIrrigationPlan() {
        DistrictProfile district = chooseDistrict();
        System.out.println("\n--- Irrigation plan for " + district.name + " ---");
        System.out.println("1. First week after transplanting: maintain 2-3 cm water.");
        System.out.println("2. Tillering / vegetative stage: target about 5 cm, with safe intermittent drying when suitable.");
        System.out.println("3. Flowering: prevent water stress; inspect the field at least daily.");
        System.out.println("4. Grain filling: maintain a shallow layer and respond to weather.");
        System.out.println("5. Before harvest: drain completely about 10 days before expected harvest.");
        System.out.println("Local note: " + district.zone + " fields should adjust this plan to soil, canal supply, and rainfall.");
    }

    private static void showHealthAdvisory() {
        System.out.println("\nCommon options: " + String.join(", ", ADVISORIES.keySet()));
        String query = readText("Enter a disease or pest name (or 'list'): ");
        if (query.equalsIgnoreCase("list")) {
            for (Advisory advisory : ADVISORIES.values()) {
                System.out.println("- " + advisory.name);
            }
            return;
        }

        Advisory advisory = ADVISORIES.get(query.toLowerCase(Locale.ROOT));
        if (advisory == null) {
            System.out.println("No exact match. Take a clear photo of the leaf, sheath, or grain and ask a verified agronomist.");
            return;
        }
        System.out.println("\n" + advisory.name + " / " + kannadaLabel(advisory.name));
        System.out.println("Symptoms: " + advisory.symptoms);
        System.out.println("What to do now: " + advisory.action);
        System.out.println("Chemical option: " + advisory.chemical);
        System.out.println("Lower-chemical option: " + advisory.organic);
        System.out.println("Safety: Confirm the diagnosis, use protective equipment, follow the product label, and keep people and livestock away during spraying.");
    }

    private static void showWaterDecision() {
        System.out.println("\n--- Smart water controller decision ---");
        double depth = readDouble("Current water depth in cm: ", 0, 100);
        String stage = readText("Growth stage (first-week, vegetative, flowering, grain-filling, pre-harvest): ");
        boolean rainExpected = readYesNo("Is useful rain expected soon? (y/n): ");
        double target = targetDepth(stage);
        boolean preHarvest = stage.toLowerCase(Locale.ROOT).contains("pre-harvest");

        System.out.printf(Locale.ROOT, "Target depth: %.1f cm%n", target);
        if (preHarvest) {
            System.out.println("PUMP OFF / DRAIN: keep the field drained for the final 10 days.");
        } else if (rainExpected && depth >= target) {
            System.out.println("PUMP OFF: delay irrigation because rain is expected and current depth is adequate.");
        } else if (depth < target) {
            System.out.println("PUMP ON: irrigate in short cycles, then re-measure to avoid overfilling.");
        } else {
            System.out.println("PUMP OFF: target depth is met; continue monitoring.");
        }
        if (stage.toLowerCase(Locale.ROOT).contains("flowering") && depth < 5) {
            System.out.println("ALERT: flowering is sensitive to water stress—inspect the pump and inlet now.");
        }
        System.out.println("IoT note: an ESP32 can apply this rule using a calibrated float or ultrasonic sensor and a protected relay.");
    }

    private static double targetDepth(String stage) {
        String normalized = stage.toLowerCase(Locale.ROOT);
        if (normalized.contains("first")) {
            return 2.5;
        }
        if (normalized.contains("pre-harvest")) {
            return 0;
        }
        return 5;
    }

    private static DistrictProfile chooseDistrict() {
        List<String> names = Arrays.asList("Mandya", "Raichur", "Koppal", "Shivamogga");
        System.out.println("Districts: " + String.join(", ", names));
        while (true) {
            String input = readText("Enter district: ");
            for (String name : names) {
                if (name.equalsIgnoreCase(input)) {
                    return DISTRICTS.get(name);
                }
            }
            System.out.println("Please choose one of the listed districts.");
        }
    }

    private static String chooseSeason() {
        while (true) {
            String season = readText("Season (Kharif/Summer): ");
            if (season.equalsIgnoreCase("kharif")) {
                return "Kharif";
            }
            if (season.equalsIgnoreCase("summer")) {
                return "Summer";
            }
            System.out.println("Please enter Kharif or Summer.");
        }
    }

    private static String kannadaLabel(String name) {
        if (name.equals("Leaf Blast")) {
            return "ಎಲೆ ಅಂಗಮಾರಿ";
        }
        if (name.equals("Brown Spot")) {
            return "ಕಂದು ಮಚ್ಚೆ ರೋಗ";
        }
        if (name.equals("Sheath Blight")) {
            return "ಕವಚ ಅಂಗಮಾರಿ";
        }
        if (name.equals("Stem Borer")) {
            return "ಕಾಂಡ ಕೊರೆಯುವ ಹುಳು";
        }
        return "ಸ್ಥಳೀಯ ಸಲಹೆ ಅಗತ್ಯ";
    }

    private static String readText(String prompt) {
        System.out.print(prompt);
        return INPUT.nextLine().trim();
    }

    private static int readInt(String prompt, int min, int max) {
        while (true) {
            try {
                int value = Integer.parseInt(readText(prompt));
                if (value >= min && value <= max) {
                    return value;
                }
            } catch (NumberFormatException ignored) {
                // Show one friendly validation message below.
            }
            System.out.println("Enter a number from " + min + " to " + max + ".");
        }
    }

    private static double readDouble(String prompt, double min, double max) {
        while (true) {
            try {
                double value = Double.parseDouble(readText(prompt));
                if (value >= min && value <= max) {
                    return value;
                }
            } catch (NumberFormatException ignored) {
                // Show one friendly validation message below.
            }
            System.out.println("Enter a value between " + min + " and " + max + ".");
        }
    }

    private static boolean readYesNo(String prompt) {
        while (true) {
            String answer = readText(prompt);
            if (answer.equalsIgnoreCase("y") || answer.equalsIgnoreCase("yes")) {
                return true;
            }
            if (answer.equalsIgnoreCase("n") || answer.equalsIgnoreCase("no")) {
                return false;
            }
            System.out.println("Please answer y or n.");
        }
    }

    private static class DistrictProfile {

        private final String name;
        private final String zone;
        private final String nursery;
        private final String transplanting;
        private final String harvest;

        DistrictProfile(String name, String zone, String nursery, String transplanting, String harvest) {
            this.name = name;
            this.zone = zone;
            this.nursery = nursery;
            this.transplanting = transplanting;
            this.harvest = harvest;
        }
    }

    private static class Advisory {

        private final String name;
        private final String symptoms;
        private final String action;
        private final String chemical;
        private final String organic;

        Advisory(String name, String symptoms, String action, String chemical, String organic) {
            this.name = name;
            this.symptoms = symptoms;
            this.action = action;
            this.chemical = chemical;
            this.organic = organic;
        }
    }
}
