"""Create LlamaIndex Workflow test data for Edda Workflow Manager."""

import asyncio
from pathlib import Path

from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step

from edda import EddaApp, WorkflowContext, workflow
from edda.integrations.llamaindex import DurableWorkflowRunner


# =============================================================================
# Event Definitions
# =============================================================================


class OrderReceivedEvent(Event):
    """Event when order is received."""

    order_id: str
    amount: float


class ProcessingCompleteEvent(Event):
    """Event when processing is complete."""

    order_id: str
    status: str


# =============================================================================
# LlamaIndex Workflow Definition
# =============================================================================


class OrderWorkflow(Workflow):
    """Simple order processing workflow."""

    @step
    async def receive_order(self, ctx, ev: StartEvent) -> OrderReceivedEvent:
        """Receive and validate the order."""
        print(f"  [receive_order] Received order: {ev.order_id}")
        await asyncio.sleep(2)  # Slow down for Live Viewer testing
        return OrderReceivedEvent(order_id=ev.order_id, amount=ev.amount)

    @step
    async def process_order(self, ctx, ev: OrderReceivedEvent) -> ProcessingCompleteEvent:
        """Process the order (simulate with delay)."""
        print(f"  [process_order] Processing order {ev.order_id}...")
        await asyncio.sleep(3)  # Slow down for Live Viewer testing
        print(f"  [process_order] Order {ev.order_id} processed!")
        return ProcessingCompleteEvent(order_id=ev.order_id, status="processed")

    @step
    async def complete_order(self, ctx, ev: ProcessingCompleteEvent) -> StopEvent:
        """Complete the order."""
        print(f"  [complete_order] Completing order {ev.order_id}")
        await asyncio.sleep(2)  # Slow down for Live Viewer testing
        return StopEvent(
            result={
                "order_id": ev.order_id,
                "status": ev.status,
                "message": "Order completed successfully",
            }
        )


# =============================================================================
# Durable Runner Setup
# =============================================================================

runner = DurableWorkflowRunner(OrderWorkflow)


# =============================================================================
# Edda Workflow
# =============================================================================


@workflow
async def order_workflow(ctx: WorkflowContext, order_id: str, amount: float) -> dict:
    """Process an order using durable LlamaIndex workflow."""
    print(f"\n=== Starting order workflow for {order_id} ===")
    result = await runner.run(ctx, order_id=order_id, amount=amount)
    print(f"=== Order workflow completed: {result} ===\n")
    return result


# =============================================================================
# Main
# =============================================================================


async def main():
    """Create test data."""
    db_path = Path(__file__).parent / "llamaindex_test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    print("=" * 60)
    print("Creating LlamaIndex Workflow Test Data")
    print(f"Database: {db_path}")
    print("=" * 60)

    # Remove old database if exists
    if db_path.exists():
        db_path.unlink()
        print("Removed existing database")

    # Create and initialize the app
    app = EddaApp(
        service_name="order-service",
        db_url=db_url,
    )
    await app.initialize()

    try:
        # Create multiple workflow instances
        orders = [
            ("ORD-001", 99.99),
            ("ORD-002", 149.50),
            ("ORD-003", 275.00),
            ("ORD-004", 50.00),
            ("ORD-005", 999.99),
        ]

        instance_ids = []
        for order_id, amount in orders:
            print(f"\n[Starting workflow for {order_id}...]")
            instance_id = await order_workflow.start(
                order_id=order_id,
                amount=amount,
            )
            instance_ids.append(instance_id)
            print(f"Instance: {instance_id}")

        # Wait for completion
        print("\n[Waiting for workflows to complete...]")
        await asyncio.sleep(2)

        # Show results
        print("\n" + "=" * 60)
        print("Created Workflow Instances:")
        print("=" * 60)

        for instance_id in instance_ids:
            instance = await app.storage.get_instance(instance_id)
            print(f"  {instance_id[:12]}... - Status: {instance['status']}")

        print(f"\nDatabase saved to: {db_path}")
        print("\nTo test with Edda Workflow Manager:")
        print(f"  uv run python examples/edda_workflow_manager/main.py --db {db_url}")

    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
