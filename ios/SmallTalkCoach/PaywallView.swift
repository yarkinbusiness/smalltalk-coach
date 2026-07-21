import StoreKit
import SwiftUI

struct PaywallView: View {
    @ObservedObject private var purchaseManager: PurchaseManager
    @Environment(\.dismiss) private var dismiss

    init(purchaseManager: PurchaseManager) {
        self.purchaseManager = purchaseManager
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Unlock Units 2–4 and keep building your small-talk skills.")
                        .foregroundStyle(.secondary)
                }

                Section("Choose a plan") {
                    if purchaseManager.products.isEmpty {
                        ProgressView("Loading plans…")
                    } else {
                        ForEach(purchaseManager.products, id: \.id) { product in
                            Button {
                                Task { await purchaseManager.purchase(product) }
                            } label: {
                                HStack {
                                    Text(product.displayName)
                                    Spacer()
                                    Text(product.displayPrice)
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .disabled(purchaseManager.purchaseState == .purchasing)
                        }
                    }
                }

                Section {
                    Button("Restore Purchases") {
                        Task { await purchaseManager.restore() }
                    }
                    .disabled(purchaseManager.purchaseState == .purchasing)
                }

                switch purchaseManager.purchaseState {
                case .idle:
                    EmptyView()
                case .purchasing:
                    ProgressView("Contacting the store…")
                case .pending:
                    Text("Purchase awaiting approval.")
                        .foregroundStyle(.secondary)
                case .failed(let message):
                    Text(message)
                        .foregroundStyle(.red)
                }
            }
            .navigationTitle("SmallTalk Coach Premium")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Close") { dismiss() }
                }
            }
        }
        .task {
            await purchaseManager.loadProducts()
        }
        .onChange(of: purchaseManager.isPremium) { _, isPremium in
            if isPremium {
                dismiss()
            }
        }
    }
}
