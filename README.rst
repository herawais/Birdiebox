Odoo PrintNode Base module
==========================


Change Log
##########

|

* 1.6 (2021-04-16)
    - Added  possibility to define Universal Print Attachments Wizard for any model in the Odoo.
    - (Experimental) Added settings to allow auto-printing of shipping labels from attachments. To support shipping carriers implemented not according to Odoo standards.
    - Fix printing error when sending to PrintNode many documents at the same time.

* 1.5.2 (2021-03-26)
    - Added print scenarios to print "Lot labels" or "Product Labels" in real time when receiving items.
      It allows either to print single label (to stick on box) OR multiple labels equal to quantity of received items

* 1.5.1 (2021-03-13)
    - Fixed an issue with Report Download controller interruption
    - Fixed an issue with printing document with scenarios for different report model

* 1.5 (2021-02-25)
    - Removed warning with Unit tests when installing module on Odoo.sh.
    - Added new scenario: print product labels for validated transfers.
    - Added new scenario: print picking document after sale order confirmation.

* 1.4.2 (2021-01-13)
    - Added possibility to view the number of prints consumed from the printnode account (experimental).

* 1.4.1 (2021-01-12)
   - Updating the "printed" flag on stock.picking model after Print Scenario execution.

* 1.4 (2020-12-21)
    - Added possibility to define number of copies to be printed in "Print Action Button" menu.
    - Added Print Scenarios which allows to print reports on pre-programmed actions.

* 1.3.1 (2020-11-10)
    - Added constraints not to allow creation of not valid "Print Action Buttons" and "Methods".
    - On product label printing wizard pre-select printer in case only 1 suitable was found.

* 1.3 (2020-10-09)
    - Added possibility to print product labels while processing Incoming Shipment into your Warehouse.
      Also you can mass print product labels directly from individual product or product list.
    - Show info message on User Preferences in case there are User Rules that can redefine Default user Printer.
    - Added examples to Print Action menu for some typical use cases for Delivery Order and Sales Order printing.

* 1.2.1 (2020-10-07)
    - When direct-printing via Print menu, there is popup message informing user about successful printing.
      Now this message can be disabled via Settings.
    - Fixed issue with wrong Delivery Slip printing, after backorder creation.

* 1.2 (2020-07-28)
    -  Make Printer non-required in "Print action buttons" menu. If not defined, than printer will be selected
       based on user or company printer setting.
    -  Added Support for Odoo Enterprise Barcode Interface. Now it is compatible with "Print action buttons" menu.
    -  "Print action buttons" menu now allows to select filter for records, where reports should be auto-printed.
       E.g. Print Delivery Slip only for Pickings of Type = Delivery Order.

* 1.1 (2020-07-24)
    -  Added Support for automatic/manual printing of Shipping Labels.
       Supporting all Odoo Enterprise included Delivery Carries (FedEx, USPS, UPS, bpost and etc.).
       Also Supporting all custom carrier integration modules that are written according to Odoo Standards.

* 1.0 (2020-07-20)
    - Initial version providing robust integration of Odoo with PrintNode for automatic printing.

|
