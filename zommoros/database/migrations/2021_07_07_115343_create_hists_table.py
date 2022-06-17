from orator.migrations import Migration


class CreateHistsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('hists') as table:
            table.increments('id')
            table.integer('run_list_id')
            table.string('datetime')
            table.string('open')
            table.string('high')
            table.string('low')
            table.string('close')
            table.string('volume')
            table.timestamps()

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('hists')
