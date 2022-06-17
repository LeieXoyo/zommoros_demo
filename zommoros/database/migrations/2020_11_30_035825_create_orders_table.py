from orator.migrations import Migration


class CreateOrdersTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('orders') as table:
            table.increments('id')
            table.string('order_id').unique()
            table.string('datetime').nullable()
            table.string('symbol').nullable()
            table.string('type').nullable()
            table.string('side').nullable()
            table.string('price').nullable()
            table.string('average').nullable()
            table.string('cost').nullable()
            table.string('amount').nullable()
            table.string('filled').nullable()
            table.string('remaining').nullable()
            table.string('status').nullable()
            table.string('fee').nullable()
            table.long_text('json')
            table.timestamps()

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('orders')
