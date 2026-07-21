import Combine
import StoreKit

enum PurchaseState: Equatable {
    case idle
    case purchasing
    case pending
    case failed(String)
}

enum PurchaseOutcome: Equatable {
    case userCancelled
    case pending

    var purchaseState: PurchaseState {
        switch self {
        case .userCancelled:
            .idle
        case .pending:
            .pending
        }
    }
}

enum LessonPaywallAccess {
    static func isGated(paywallEnabled: Bool, unit: Int, isPremium: Bool) -> Bool {
        paywallEnabled && unit >= 2 && !isPremium
    }
}

@MainActor
final class PurchaseManager: ObservableObject {
    static let productIDs = [
        "com.smalltalkcoach.app.premium.monthly",
        "com.smalltalkcoach.app.premium.yearly"
    ]

    @Published private(set) var isPremium = false
    @Published private(set) var products: [Product] = []
    @Published private(set) var purchaseState: PurchaseState = .idle
    @Published private(set) var hasLoadedEntitlements = false

    private var updatesTask: Task<Void, Never>?

    init() {
        updatesTask = Task { [weak self] in
            for await verification in Transaction.updates {
                guard let self else { return }
                do {
                    let transaction = try Self.checkVerified(verification)
                    await self.refreshEntitlements()
                    await transaction.finish()
                } catch {
                    // Unverified updates must not alter entitlement state or be finished.
                }
            }
        }

        Task { [weak self] in
            await self?.refreshEntitlements()
        }
    }

    deinit {
        updatesTask?.cancel()
    }

    func loadProducts() async {
        do {
            let loadedProducts = try await Product.products(for: Self.productIDs)
            products = loadedProducts.sorted { $0.id < $1.id }
        } catch {
            purchaseState = .failed(error.localizedDescription)
        }
    }

    func purchase(_ product: Product) async {
        purchaseState = .purchasing

        do {
            switch try await product.purchase() {
            case .success(let verification):
                let transaction = try Self.checkVerified(verification)
                guard Self.productIDs.contains(transaction.productID) else {
                    purchaseState = .failed("This product is not available for Premium.")
                    return
                }

                await refreshEntitlements()
                guard isPremium else {
                    purchaseState = .failed("We couldn’t confirm your Premium access yet.")
                    return
                }

                await transaction.finish()
                purchaseState = .idle
            case .userCancelled:
                purchaseState = PurchaseOutcome.userCancelled.purchaseState
            case .pending:
                purchaseState = PurchaseOutcome.pending.purchaseState
            @unknown default:
                purchaseState = .failed("This purchase could not be completed.")
            }
        } catch {
            purchaseState = .failed(error.localizedDescription)
        }
    }

    func restore() async {
        purchaseState = .purchasing
        do {
            try await AppStore.sync()
            await refreshEntitlements()
            purchaseState = .idle
        } catch {
            purchaseState = .failed(error.localizedDescription)
        }
    }

    func refreshEntitlements() async {
        var premiumEntitlementFound = false

        for await verification in Transaction.currentEntitlements {
            guard let transaction = try? Self.checkVerified(verification) else { continue }
            if Self.productIDs.contains(transaction.productID) {
                premiumEntitlementFound = true
            }
        }

        isPremium = premiumEntitlementFound
        hasLoadedEntitlements = true
    }

    private static func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified(_, let error):
            throw error
        case .verified(let safe):
            return safe
        }
    }
}
