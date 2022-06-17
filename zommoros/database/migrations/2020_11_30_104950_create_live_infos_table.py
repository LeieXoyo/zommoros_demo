from orator.migrations import Migration


class CreateLiveInfosTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('live_infos') as table:
            table.increments('id')
            table.integer('run_list_id')
            table.string('symbol')
            table.string('side')
            table.string('open_datetime').nullable()
            table.string('close_datetime').nullable()
            table.string('open_price').nullable()
            table.string('close_price').nullable()
            table.string('leverage').nullable()
            table.string('liquidation_price').nullable()
            table.string('size').nullable()
            table.string('profit').nullable()
            table.string('value').nullable()
            table.timestamps()

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('live_infos')
